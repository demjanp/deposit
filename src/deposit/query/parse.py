import re
import ast

def get_new_key(prefix, substr, done):
	
	key = "_%s1_" % (prefix)
	n = 1
	while (key in done) or (key in substr):
		n += 1
		key = "_%s%d_" % (prefix, n)
	return key

def add_bracketed(clsname, descrname, prefix, substr, bracketed, lookup):
	
	if isinstance(clsname, str):
		clsname = clsname.strip("[]")
	
	if (clsname, descrname) in lookup:
		key = lookup[(clsname, descrname)]
	else:
		key = get_new_key(prefix, substr, bracketed)
		bracketed[key] = (clsname, descrname)
		lookup[(clsname, descrname)] = key
	
	return key

def str_to_key(substr):
	
	substr = tuple(substr.split("."))
	if len(substr) == 1:
		return (substr[0], None)
	return substr

def remove_quoted(substr):
	# returns substr, quoted = {key: quoted substr, ...}
	
	quoted = {}
	while True:
		found = False
		for m in re.finditer(r"(['\"])(.*?)\1", substr):
			i, j = m.start(0), m.end(0)
			key = get_new_key("QU", substr, quoted)
			quoted[key] = substr[i:j]
			substr = substr[:i] + " %s " % (key) + substr[j:]
			found = True
			break
		if not found:
			break
	
	return substr, quoted

def remove_bracketed_selects(substr, classes, descriptors):
	# returns substr, bracketed = {key: (class, descriptor), ...}
	
	def process_found(substr_cleaned, i, j, names):
		
		if substr_cleaned[:i].endswith("*."):
			names.append([i-2, i-1, "*", False])
			substr_cleaned = substr_cleaned[:i-2] + " " + substr_cleaned[i-1:]
		if substr_cleaned[j:].startswith(".*"):
			names.append([j+1, j+2, "*", False])
			substr_cleaned = substr_cleaned[:j+1] + " " + substr_cleaned[j+2:]
		
		return substr_cleaned
	
	bracketed = {}
	done = {}
	
	substr_cleaned = substr
	names = []  # [[i, j, text, is_bracketed], ...]
	
	where_index = substr_cleaned.find("WHERE")
	
	for m in re.finditer(r"OBJ+\(.*?\)", substr_cleaned):
		i, j = m.start(0), m.end(0)
		if i > where_index:
			continue
		ids = [id_.strip() for id_ in substr_cleaned[i+4:j-1].split(",")]
		if not False in [id_.isdigit() for id_ in ids]:
			names.append([i, j, tuple([int(id_) for id_ in ids]), True])
			substr_cleaned = substr_cleaned[:i] + (j-i)*" " + substr_cleaned[j:]
			substr_cleaned = process_found(substr_cleaned, i, j, names)
	
	for clsname in sorted(list(classes), key = lambda name: len(name))[::-1]:
		for m in re.finditer(r"(\A|[^a-zA-Z0-9_])(%s)([^a-zA-Z0-9_]|\Z)" % (clsname), substr_cleaned):
			i, j = m.start(0), m.end(0)
			found = False
			if (substr_cleaned[i] == "[") and (substr_cleaned[j-1] == "]"):
				names.append([i, j, substr_cleaned[i:j], True])
				substr_cleaned = substr_cleaned[:i] + (j-i)*" " + substr_cleaned[j:]
				found = True
			else:
				if substr_cleaned[i:].startswith(clsname):
					i -= 1
				if substr_cleaned[:j].endswith(clsname):
					j += 1
				if substr_cleaned[i+1:j-1].isidentifier():
					i += 1
					j -= 1
					names.append([i, j, substr_cleaned[i:j], False])
					substr_cleaned = substr_cleaned[:i] + len(substr_cleaned[i:j])*" " + substr_cleaned[j:]
					found = True
			if found:
				substr_cleaned = process_found(substr_cleaned, i, j, names)
	
	fragments = []  # [[text, is_class, is_bracketed], ...]
	j_last = 0
	for i, j, name, is_bracketed in sorted(names, key = lambda row: row[0]):
		if i > j_last:
			fragments.append([substr_cleaned[j_last:i], False, False])
		fragments.append([name, True, is_bracketed])
		j_last = j
	if j_last < len(substr_cleaned):
		fragments.append([substr_cleaned[j_last:], False, False])
	
	checkstr = ""
	for text, is_class, _ in fragments:
		if is_class:
			checkstr += "C"
		elif text == ".":
			checkstr += "."
		else:
			checkstr += "X"
	
	descriptors = descriptors.union({"*"})
	
	collect = []
	while fragments:
		if checkstr.startswith("C.C.C"):
			# not a SELECT (probably a relation)
			for i in range(5):
				text, _, _ = fragments.pop(0)
				collect.append(text)
			checkstr = checkstr[5:]
		elif checkstr.startswith("C.C"):
			clsname, descrname = fragments[0][0], fragments[2][0].strip("[]")
			clsname = clsname.strip("[]") if isinstance(clsname, str) else clsname
			if (descrname in descriptors) and (fragments[0][2] or fragments[2][2]):
				# second class is a descriptor and one of them is bracketed
				key = add_bracketed(clsname, descrname, "VAR", substr, bracketed, done)
				collect += " %s " % (key)
			else:
				collect += [text for text, _, _ in fragments[:3]]
			fragments = fragments[3:]
			checkstr = checkstr[3:]
		elif checkstr.startswith("CX") and fragments[1][0].strip().startswith("."):
			collect += [text for text, _, _ in fragments[:3]]
			fragments = fragments[3:]
			checkstr = checkstr[3:]
		elif checkstr.startswith("C") and fragments[0][2]:
			# bracketed class without a descriptor
			key = add_bracketed(fragments[0][0], None, "VAR", substr, bracketed, done)
			collect += " %s " % (key)
			fragments = fragments[1:]
			checkstr = checkstr[1:]
		else:
			text, _, _ = fragments.pop(0)
			collect.append(text)
			checkstr = checkstr[1:]
	collect = ["OBJ(%s)" % (",".join([str(id_) for id_ in item])) if isinstance(item, tuple) else item for item in collect]
	substr = "".join(collect)
	
	return substr, bracketed

def remove_classless(substr, classes):
	
	classless = set()
	while True:
		found = False
		for m in re.finditer(r"!\*\.", substr):
			i, j = m.start(0), m.end(0)
			key = get_new_key("CL", substr, classless.union(classes))
			classless.add(key)
			substr = substr[:i] + key + substr[j-1:]
			found = True
			break
		if not found:
			break
	
	return substr, classless

def remove_bracketed_all(substr):
	# returns substr, bracketed = {key: bracketed substr, ...}
	
	bracketed = {}
	while True:
		found = False
		for m in re.finditer(r"OBJ+\(.*?\)", substr):
			i, j = m.start(0), m.end(0)
			ids = [id_.strip() for id_ in substr[i+4:j-1].split(",")]
			if not False in [id_.isdigit() for id_ in ids]:
				key = get_new_key("BA", substr, bracketed)
				bracketed[key] = tuple([int(id_) for id_ in ids])
				substr = substr[:i] + key + substr[j:]
				found = True
				break
		for m in re.finditer(r"\[.*?\]", substr):
			i, j = m.start(0), m.end(0)
			key = get_new_key("BA", substr, bracketed)
			bracketed[key] = substr[i:j]
			substr = substr[:i] + key + substr[j:]
			found = True
			break
		if not found:
			break
	
	return substr, bracketed

def replace_bracketed(substr, bracketed):
	
	for key in bracketed:
		data = bracketed[key]
		if isinstance(data, tuple):
			data = "OBJ(%s)" % (",".join([str(obj_id) for obj_id in data]))
		substr = substr.replace(key, data)
	return substr

class SelectsToVarsTransformer1(ast.NodeTransformer):
	
	def __init__(self, substr, classes, descriptors, bracketed_selects):
		# classes = {class_name, ...}
		# descriptors = {descriptor_name, ...}
		# bracketed_selects = {key: (class, descriptor), ...}
		
		ast.NodeTransformer.__init__(self)
		
		self._done = {}  # {(class_name, descriptor_name): variable_name, ...}
		self.selects = bracketed_selects  # {key: (class, descriptor), ...}
		
		self._substr = substr
		self._classes = classes
		self._descriptors = descriptors
		
		for name in self.selects:
			key = self.selects[name]
			self._done[key] = name
	
	def visit_Attribute(self, node):
		
		self.generic_visit(node)
		
		if (type(node.value) is ast.Name) and \
			(node.value.id not in __builtins__) and \
			(node.value.id in self._classes) and \
			(node.attr not in __builtins__) and \
			(node.attr in self._descriptors):
				name = add_bracketed(node.value.id, node.attr, "VAR", self._substr, self.selects, self._done)
				return ast.Name(id = name, ctx = node.ctx)
		
		return node

class SelectsToVarsTransformer2(SelectsToVarsTransformer1):
	
	def visit_Name(self, node):
		
		name = node.id
		if (name not in __builtins__) and (name in self._classes):
			name = add_bracketed(name, None, "VAR", self._substr, self.selects, self._done)
		
		return ast.Name(id = name, ctx = node.ctx)
	
	def visit_Attribute(self, node):
		
		return node

def extract_expr_vars(substr, classes, descriptors, bracketed_selects):
	# classes = {name, ...}
	# descriptors = {name, ...}
	# bracketed_selects = {key: (class, descriptor), ...}
	
	substr, classless = remove_classless(substr, classes)
	
	tree = ast.parse(substr)
	# find and replace Class.Descriptor occurences in substr
	transformer = SelectsToVarsTransformer1(substr, classes.union(classless), descriptors, bracketed_selects)
	tree = transformer.visit(tree)
	# find and replace Class occurences in substr
	transformer = SelectsToVarsTransformer2(substr, classes.union(classless), descriptors, bracketed_selects)
	tree = transformer.visit(tree)
	
	expr = ast.unparse(tree)
	vars = transformer.selects.copy()
	
	for name in vars:
		if vars[name][0] in classless:
			cls, descr = vars[name]
			vars[name] = ("!*", descr)
	
	return expr, vars

class Parse(object):
	
	KEYWORDS = ["SELECT", "COUNT", "SUM", "AS", "WHERE", "GROUP BY"]

	def __init__(self, querystr, classes, descriptors):
		# classes = {name, ...}
		# descriptors = {name, ...}
		# querystr = "SELECT [select1], [select2], COUNT([select1]) AS [alias], SUM([select1]) AS [alias], ... WHERE [conditions expression] GROUP BY [select1], [select2], ..."
		#	select = Class or Class.Descriptor
		#		Class can be Class name or OBJ(id) to specify an Object by its id
		#	conditions = python expression; e.g. Class.Descriptor > 3 or Class is not None
		#		a condition can be RELATED(Class1, Class2, 'label', chained=True/False)
		#	use [name with spaces] to escape class, descriptor, relation or alias names containing spaces or KEYWORDS
		
		self.querystr = querystr
		self.classes = classes
		self.descriptors = descriptors
		
		self.columns = []  # [(class_name, descriptor_name), (None, alias), ...]
		self.selects = []  # [(class_name, descriptor_name), ...]
		self.group_by = []  # [(class_name, descriptor_name), ...]
		self.counts = []  # [(alias, class_name, descriptor_name), ...]
		self.sums = []  # [(alias, class_name, descriptor_name), ...]
		self.relations = []  # [(class1, relation, class2), ...]
		self.where_expr = ""
		self.where_vars = {}  # {name: (class, descriptor), ...}
		self.classes_used = []  # [name, ...]
		
		querystr, quoted = remove_quoted(self.querystr)
		querystr, bracketed_selects = remove_bracketed_selects(querystr, self.classes, self.descriptors)
		querystr, bracketed_other = remove_bracketed_all(querystr)
		
		# convert old-style RELATED segments to WHERE RELATED() format
		relations = []
		i, j, k = 0, 0, 0
		for m in re.finditer(r"(?i)\bRELATED\b", querystr):
			i = m.start(0)
			j = m.end(0)
			for keyword in self.KEYWORDS:
				k = querystr.find(keyword, j)
				if k != -1:
					break
			else:
				k = len(querystr)
			substr = querystr[j:k].strip().strip(",").strip()
			for chain in substr.split(","):
				chain = chain.strip().split(".")
				if len(chain) == 3:
					relations.append(chain)
		where_txt = None
		where_found = False
		if relations:
			where_txt = "(%s)" % " and ".join(["RELATED(%s, %s, '%s')" % (chain[0], chain[2], chain[1]) for chain in relations])
			querystr = querystr[:i] + querystr[k:]
		
		collect = []
		for keyword in self.KEYWORDS:
			for m in re.finditer(r"(?i)\b%s\b" % (keyword), querystr):
				i, j = m.start(0), m.end(0)
				collect.append((i, j, keyword))
		collect = sorted(collect)
		collect2 = []
		for idx in range(len(collect)):
			i, j, keyword = collect[idx]
			if idx < len(collect) - 1:
				k = collect[idx + 1][0]
			else:
				k = len(querystr)
			collect2.append((keyword, j, k))
		collect = collect2
		collect2 = None
		
		while collect:
			keyword, i, j = collect.pop(0)
			substr = querystr[i:j].strip().strip(",").strip()
			
			if keyword in ["SELECT", "GROUP BY"]:
				for name in substr.split(","):
					name = name.strip()
					if name in bracketed_selects:
						item = bracketed_selects[name]
					else:
						item = str_to_key(name)
					if keyword == "SELECT":
						self.selects.append(item)
						self.columns.append(item)
					else:
						self.group_by.append(item)
			
			elif keyword in ["COUNT", "SUM"]:
				name = substr.strip("()").strip()
				if name in bracketed_selects:
					class_name, descriptor_name = bracketed_selects[name]
				else:
					class_name, descriptor_name = str_to_key(name)
				if collect and (collect[0][0] == "AS"):
					_, i, j = collect.pop(0)
					alias = querystr[i:j]
					alias = replace_bracketed(alias, bracketed_other)
					alias = alias.strip().strip(",").strip()
					class_name, descriptor_name, alias = [(item.strip("[]") if item else None) for item in [class_name, descriptor_name, alias]]
					if keyword == "COUNT":
						self.counts.append((alias, class_name, descriptor_name))
					else:
						self.sums.append((alias, class_name, descriptor_name))
					self.columns.append((None, alias))
			elif keyword == "WHERE":
				if where_txt:
					substr = "%s and (%s)" % (where_txt, substr)
				where_found = True
				substr = replace_bracketed(substr, bracketed_other)
				self.where_expr, self.where_vars = extract_expr_vars(substr, self.classes, self.descriptors, bracketed_selects)
		
		if where_txt and not where_found:
			substr = replace_bracketed(where_txt, bracketed_other)
			self.where_expr, self.where_vars = extract_expr_vars(substr, self.classes, self.descriptors, bracketed_selects)
		
		for key in quoted:
			self.where_expr = self.where_expr.replace(key, quoted[key])
		
		# Find the patterns "RELATED(Class1, Class2, Relation)" in self.where_expr and add them to self.relations
		for m in re.finditer(r"RELATED\((.*?), (.*?), '(.*?)'(?:, .*?)?\)", self.where_expr):
			class1, class2, label = m.groups()
			if class1 in self.where_vars:
				class1 = self.where_vars[class1][0]
			if class2 in self.where_vars:
				class2 = self.where_vars[class2][0]
			self.relations.append((class1, label, class2))
		
		for class_name, _ in self.selects + self.group_by:
			if (class_name is not None) and (class_name not in self.classes_used):
				self.classes_used.append(class_name)
		for _, class_name, _ in self.counts + self.sums:
			if (class_name is not None) and (class_name not in self.classes_used):
				self.classes_used.append(class_name)
		for class_name1, _, class_name2 in self.relations:
			for class_name in [class_name1, class_name2]:
				if (class_name is not None) and (class_name not in self.classes_used):
					self.classes_used.append(class_name)
		for name in self.where_vars:
			class_name = self.where_vars[name][0]
			if class_name not in self.classes_used:
				self.classes_used.append(class_name)
			
