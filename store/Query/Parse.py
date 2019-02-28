from numbers import Number

def find_index(cls):
	# returns class_name, index
	
	idx1, idx2 = cls.find("["), cls.find("]")
	if (idx1 == -1) or (idx2 == -1):
		return cls, -1
	index = cls[idx1+1:idx2]
	if index.isnumeric():
		return cls[:idx1], int(index)
	return cls, -1

def find_quotes(qry):
	# returns eval_str, quotes
	# eval_str = "[text] %(q0)s [text] %(q1)s [text]"
	# quotes = {"q0": "[text]", "q1": "[text]", ...}
	
	evals = []
	quotes = {}
	q = 0
	i0 = 0
	to_find = None
	for i in range(len(qry)):
		if qry[i] == to_find:
			quotes["q%d" % q] = qry[i0:i]
			q += 1
			i0 = i + 1
			to_find = None
		elif qry[i] == "\"":
			evals.append(qry[i0:i])
			i0 = i + 1
			to_find = qry[i]
		elif i == len(qry) - 1:
			evals.append(qry[i0:])
	
	eval_str = ""
	for i, ev in enumerate(evals):
		eval_str += ev
		if i < len(quotes):
			eval_str += "%%(q%d)s" % i
	
	return eval_str, quotes

def possible_cls_descr(word, descr):
	# descr: True if looking for a Descriptor
	
	if len(word) < 1:
		return False
	for ch in word:
		if ch in ["_","-","*","!"]:
			continue
		if (not descr) and (ch in ["[","]"]):
			continue
		if ch.isalnum():
			continue
		return False
	return True

def get_classless_object_ids(store):
	
	for id in store.objects:
		if len(store.objects[id].classes) == 0:
			yield id

def check_classes(obj, classes):
	
	if (len(obj.classes) == 0) and ("!*" in classes):
		return True
	if len(set(obj.classes.keys()).intersection(classes)) > 0:
		return True
	return False

class Select(object):
	
	def __init__(self, store, selectstr, quotes):
		
		self.store = store
		self.classes = set()  # ("!*", "[class_name]", ...)
		self.descriptors = set()  # ("[descriptor_name]", ...)
		self.classstr = ""
		self.index = -1
		
		self.set_up(selectstr, quotes)
	
	def set_up(self, selectstr, quotes):
		
		fragments = [(fragment % quotes).strip() for fragment in selectstr.split(".")]
		if (not fragments) or (len(fragments) > 2):
			return
		cls, self.index = find_index(fragments[0])
		self.classstr = cls
		if not possible_cls_descr(cls, False):
			return
		descr = None
		if len(fragments) == 2:
			descr = fragments[1]
			if not possible_cls_descr(descr, True):
				return
		if [cls, descr] == ["*", None]:
			self.classes = set(self.store.class_names)
		elif [cls, descr] == ["*", "*"]:
			self.classes = set(self.store.class_names)
			self.descriptors = set(self.store.descriptor_names)
		elif [cls, descr] == ["!*", "*"]:
			self.classes = set([cls])
			self.descriptors = set()
			for id in get_classless_object_ids(self.store):
				self.descriptors.update(self.store.objects[id].descriptors.keys())
		elif descr == "*":
			if cls.startswith("!"):
				cls = cls.strip("!")
				self.classes = set([cls1 for cls1 in self.store.class_names if cls1 != cls])
			else:
				self.classes = set([cls])
			self.descriptors = set()
			for cls in self.classes:
				self.descriptors.update(self.store.classes[cls].descriptors)
		elif cls == "*":
			self.classes = set([cls for cls in self.store.classes if descr in self.store.classes[cls].descriptors])
			self.descriptors = set([descr])
		else:
			if cls.startswith("!"):
				cls = cls.strip("!")
				self.classes = set([cls1 for cls1 in self.store.class_names if cls1 != cls])
			else:
				self.classes = set([cls])
			if descr is not None:
				self.descriptors = set([descr])
	
	def value(self, objects):
		# return value or [value, ...]; based on whether only one or multiple descriptors are specified
		
		def convert_value(value):
			
			if value is None:
				return value
			if not (isinstance(value, str) and ("_" in value)):
				try:
					value = float(value)
					if value - int(value) == 0:
						return int(value)
					return value
				except:
					pass
			return str(value)
		
		if (self.classstr not in objects) or (self.index not in objects[self.classstr]):
			return None
		values = [convert_value(objects[self.classstr][self.index].descriptors[descr].label.value) for descr in self.descriptors]
		if len(values) == 1:
			return values[0]
		return values
	
	def get_object(self, objects):
		
		if (self.classstr in objects) and (self.index in objects[self.classstr]):
			return objects[self.classstr][self.index]
		return None
	
class ObjectId(object):
	
	def __init__(self, store, classstr):
		
		self.store = store
		self.classes = set()  # ("!*", "[class_name]", ...)
		self.classstr = ""
		self.index = -1
		
		self.set_up(classstr)
	
	def set_up(self, classstr):
		
		cls, self.index = find_index(classstr)
		self.classstr = cls
		if cls.strip("!") not in self.store.class_names + ["*"]:
			return
		if cls == "*":
			self.classes = set(self.store.class_names)
		elif cls == "!*":
			self.classes = set([cls])
		elif cls.startswith("!"):
			cls = cls.strip("!")
			self.classes = set([cls1 for cls1 in self.store.class_names if cls1 != cls])
		else:
			self.classes = set([cls])
	
	def id(self, objects):
		
		if (self.classstr not in objects) or (self.index not in objects[self.classstr]):
			return None
		return objects[self.classstr][self.index].id
	
class Related(object):
	
	def __init__(self, store, relstr, quotes):
		
		self.store = store
		self.classes1 = set() # ("!*", "[class_name]", ...)
		self.classstr1 = ""
		self.index1 = -1
		self.classes2 = set() # ("!*", "[class_name]", ...)
		self.classstr2 = ""
		self.index2 = -1
		self.relation = None # "*" or "!*", "[relation_name]" or "![relation_name]"
		
		self.set_up(relstr, quotes)
	
	def set_up(self, relstr, quotes):
		
		fragments = [(fragment % quotes).strip() for fragment in relstr.split(".")]
		if len(fragments) != 3:
			return
		cls1, self.relation, cls2 = fragments
		cls1, self.index1 = find_index(cls1)
		cls2, self.index2 = find_index(cls2)
		self.classstr1 = cls1
		self.classstr2 = cls2
		valid_class_names = self.store.class_names + ["*"]
		if (cls1.strip("!") not in valid_class_names) or (cls2.strip("!") not in valid_class_names) or (self.relation.strip("!") not in (self.store.relation_names + ["*"])):
			return
		cls12 = [cls1, cls2]
		for i in range(2):
			if cls12[i][0] == "*":
				cls12[i] = set(self.store.class_names)
			elif cls12[i] == "!*":
				cls12[i] = set(["!*"])
			elif cls12[i].startswith("!"):
				cls12[i] = set([cls for cls in self.store.class_names if cls != cls12[i][1:]] + ["!*"])
			else:
				cls12[i] = set([cls12[i]])
		[self.classes1, self.classes2] = cls12
	
	def get_objects2(self, obj1):
		
		ids = set()
		if self.relation[-1] == "*":
			for rel in obj1.relations:
				ids.update(obj1.relations[rel].keys())
			if self.relation[0] == "!":	
				collect = set()
				for cls in self.classes1:
					if cls == "!*":
						collect.update([id for id in get_classless_object_ids(self.store) if not id in ids])
					else:
						collect.update([id for id in self.store.classes[cls] if id not in ids])
				ids = collect
		else:
			rel = self.relation.strip("!")
			if rel in obj1.relations:
				ids = set(obj1.relations[rel].keys())
				if self.relation[0] == "!":
					ids = set([id for id in store.objects if id not in ids])
		ids = [self.store.objects[id] for id in ids]
		return [obj for obj in ids if check_classes(obj, self.classes2)]
		
	def get_objects1(self, obj2):
		
		ids = set()
		if self.relation[-1] == "*":
			for rel in obj2.relations:
				ids.update(obj2.relations[rel].keys())
			if self.relation[0] == "!":	
				collect = set()
				for cls in self.classes2:
					if cls == "!*":
						collect.update([id for id in get_classless_object_ids(self.store) if not id in ids])
					else:
						collect.update([id for id in self.store.classes[cls] if id not in ids])
				ids = collect
		else:
			rel = self.store.reverse_relation(self.relation.strip("!"))
			if rel in obj2.relations:
				ids = set(obj2.relations[rel].keys())
				if self.relation[0] == "!":
					ids = set([id for id in store.objects if id not in ids])
		ids = [self.store.objects[id] for id in ids]
		return [obj for obj in ids if check_classes(obj, self.classes1)]
		
class Weight(object):
	
	def __init__(self, store, weightstr, quotes):
		
		self.store = store
		self.related = None
		
		self.set_up(weightstr, quotes)
	
	def set_up(self, weightstr, quotes):
		
		self.related = Related(self.store, weightstr, quotes)
		if (self.related.relation == "*") or self.related.relation.startswith("!"):
			self.related = None
		elif not (self.related.classes1 and self.related.classes2):
			self.related = None
	
	def value(self, objects):
		
		obj1 = objects[self.related.relation.classstr1][self.related.relation.index1]
		obj2 = objects[self.related.relation.classstr2][self.related.relation.index2]
		if self.related.relation in obj1.relations:
			return obj1.relations[self.related.relation].weight(obj2)
		return None
	
class Condition(object):
	
	def __init__(self, store, wherestr, quotes):
		
		self.store = store
		self.eval_str = "" # selects as: "...%(s0)s...%(s1)s..."; object ids as "...%(o0)s...%(o1)s..."; weights as: "...%(w0)s...%(w1)s..."
		self.selects = []  # [Select, ...]; in order of appearance in the eval_str
		self.object_ids = []  # [ObjectId, ...]; in order of appearance in the eval_str
		self.weights = []  # [Weight, ...]; in order of appearance in the eval_str
		self.classes = set()
		
		self.set_up(wherestr, quotes)
	
	def set_up(self, wherestr, quotes):
		# find selects (Class.Descr) in wherestr and replace them by %(s[n])s & collect them in selects
		# find object ids ( id(Class) ) in wherestr and replace them by %(o[n])s & collect them in object_ids
		# find weights ( weight(Class.relation.Class) ) in wherestr and replace them by %(w[n])s & collect them in weights
		
		def possible_cls_descr(word, descr):
			# descr: True if looking for a Descriptor
			
			if len(word) < 1:
				return False
			for ch in word:
				if ch in ["_","-","*","!"]:
					continue
				if (not descr) and (ch in ["[","]"]):
					continue
				if ch.isalnum():
					continue
				return False
			return True
		
		def possible_object_id(word):
			# id([class])
			
			if len(word) < 5:
				return False
			if not word.startswith("id("):
				return False
			if not word[-1] == ")":
				return False
			return possible_cls_descr(word[3:-1], False)
		
		def possible_weight(word):
			# weight([class].[relation].[class])
			
			if len(word) < 13:
				return False
			if not word.startswith("weight("):
				return False
			if not word[-1] == ")":
				return False
			word = word[7:-1]
			word = word.split(".")
			if len(word) < 3:
				return False
			for fragment in word:
				if not possible_cls_descr(fragment, False):
					return False
			return True
		
		# extract selects
		idx0 = -1
		extracted = []  # [[idx1, idx2, type], ...]; type = 1: Select, 2: ObjectId, 3: Weight
		while True:
			idx0 = wherestr.find(".", idx0 + 1)
			if idx0 == -1:
				break
			cls = None
			for idx1 in range(idx0):
				if possible_cls_descr(wherestr[idx1:idx0], False):
					cls = wherestr[idx1:idx0]
					break
			if cls is None:
				continue
			descr = None
			for idx2 in range(len(wherestr) - 1, idx0, -1):
				if possible_cls_descr(wherestr[idx0 + 1:idx2], True):
					descr = wherestr[idx0 + 1:idx2]
					break
			if descr is not None:
				select = Select(self.store, "%s.%s" % (cls, descr), {})
				if select.classes:
					self.selects.append(select)
					self.classes.update(select.classes)
					extracted.append([idx1, idx2, 1])
		
		# extract object ids
		idx0 = -1
		while True:
			idx0 = wherestr.find("id(", idx0 + 1)
			if idx0 == -1:
				break
			if (idx0 > 0) and (wherestr[idx0 - 1].isalnum() or (wherestr[idx0 - 1] == "_")):
				continue
			idx1 = wherestr.find(")", idx0 + 1)
			if idx1 == -1:
				break
			if possible_object_id(wherestr[idx0:idx1+1]):
				object_id = ObjectId(self.store, wherestr[idx0+3:idx1] % quotes)
				if object_id.classes:
					self.object_ids.append(object_id)
					self.classes.update(object_id.classes)
					extracted.append([idx0, idx1+1, 2])
		
		# extract weights
		idx0 = -1
		while True:
			idx0 = wherestr.find("weight(", idx0 + 1)
			if idx0 == -1:
				break
			if (idx0 > 0) and (wherestr[idx0 - 1].isalnum() or (wherestr[idx0 - 1] == "_")):
				continue
			idx1 = wherestr.find(")", idx0 + 1)
			if idx1 == -1:
				break
			if possible_weight(wherestr[idx0:idx1+1]):
				weight = Weight(self.store, wherestr[idx0+7:idx1], quotes)
				if weight.related:
					self.weights.append(weight)
					self.classes.update(weight.related.classes1)
					self.classes.update(weight.related.classes2)
					extracted.append([idx0, idx1+1, 3])
		
		idx0 = 0
		cnt_selects = 0
		cnt_object_ids = 0
		cnt_weights = 0
		for idx1, idx2, typ in extracted:
			self.eval_str += wherestr[idx0:idx1] % quotes
			if typ == 1:
				self.eval_str += "%%(s%d)s" % (cnt_selects)
				cnt_selects += 1
			elif typ == 2:
				self.eval_str += "%%(o%d)s" % (cnt_object_ids)
				cnt_object_ids += 1
			elif typ == 3:
				self.eval_str += "%%(w%d)s" % (cnt_weights)
				cnt_weights += 1
			idx0 = idx2
		self.eval_str += wherestr[idx0:] % quotes
	
	def eval(self, objects):
		# objects = {classstr: {index: DObject, ...}, ...}
		
		def get_new_var(eval_str, n):
			
			while ("_v" + str(n)) in self.eval_str:
				n += 1
			return "_v" + str(n), n
		
		vars = {} # {key: var, ...}
		values = {}  # {var: value, ...}
		n = 0
		for i, select in enumerate(self.selects):
			key = "s%d" % i
			vars[key], n = get_new_var(self.eval_str, n)
			values[vars[key]] = select.value(objects)
			n += 1
		for i, object_id in enumerate(self.object_ids):
			key = "o%d" % i
			vars[key], n = get_new_var(self.eval_str, n)
			values[vars[key]] = object_id.id(objects)
			n += 1
		for i, weight in enumerate(self.weights):
			key = "w%d" % i
			vars[key], n = get_new_var(self.eval_str, n)
			values[vars[key]] = weight.value(objects)
			n += 1
		
		return eval(self.eval_str % vars, values)
	
class Count(Condition):
	
	def __init__(self, store, countstr, alias, quotes):
		
		self.alias = alias
		Condition.__init__(self, store, countstr, quotes)
	
class Sum(object):
	
	def __init__(self, store, sumstr, alias, quotes):
		
		self.store = store
		self.alias = alias
		self.select = None
		
		self.set_up(sumstr, quotes)
	
	def set_up(self, sumstr, quotes):
		
		self.select = Select(self.store, sumstr, quotes)
		if not self.select.classes:
			self.select = None
	
	@property
	def classes(self):
		
		return self.select.classes
	
	def value(self, objects):
		
		value = self.select.value(objects)
		if value is None:
			return 0
		if isinstance(value, str):
			return 0
		if isinstance(value, list):
			value = [val for val in value if isinstance(val, Number)]
			if value:
				return sum(value)
			return 0
		if isinstance(value, Number):
			return value
	
class Parse(object):
	
	RESERVED_WORDS = ["SELECT", "RELATED", "WHERE", "COUNT", "SUM", "AS"]
	
	def __init__(self, store, querystr):
		
		self.store = store
		self.querystr = querystr
		self.selects = []  # [Select, ...]
		self.relations = []  # [Related, ...]
		self.conditions = []  # [Condition, ...]
		self.counts = []  # [Count, ...]
		self.sums = []  # [Sum, ...]
		
		self.process()
	
	def find_segments(self, qry):
		# returns segments = [[reserved_word, text], ...]
		
		qry = " " + qry
		words = {}
		for word in self.RESERVED_WORDS:
			word = " %s " % (word)
			idx0 = 0
			while True:
				idx = qry.find(word, idx0)
				if idx == -1:
					break
				words[idx] = word
				idx0 = idx + 1
		idxs = sorted(words.keys())
		segments = []
		while idxs:
			idx = idxs.pop(0)
			idx1 = idx + len(words[idx])
			idx2 = len(qry)
			if idxs:
				idx2 = idxs[0]
			segments.append([words[idx].strip(), qry[idx1:idx2]])
		return segments
	
	def process(self):
		
		qry = self.querystr.strip()
		
		# find quotes
		qry, quotes = find_quotes(qry) # quotes = {"q0": "[text]", "q1": "[text]", ...}
		
		# find segments
		segments = self.find_segments(qry) # [[reserved_word, text], ...]
		if not segments:
			return
		if segments[0][0] != "SELECT":
			return
		
		# find selects
		_, qry_select = segments.pop(0)
		self.selects = [Select(self.store, selectstr, quotes) for selectstr in qry_select.split(",")]
		self.selects = [select for select in self.selects if select.classes]
		if not self.selects:
			return
		
		# find relations
		for word, qry_related in segments:
			if word == "RELATED":
				self.relations += [Related(self.store, relstr, quotes) for relstr in qry_related.split(",")]
		self.relations = [related for related in self.relations if related.classes1 and related.classes2]
		
		# find conditions
		for word, wherestr in segments:
			if word == "WHERE":
				self.conditions.append(Condition(self.store, wherestr, quotes))
		self.conditions = [condition for condition in self.conditions if (condition.selects or condition.object_ids)]
		
		# find counts
		for i in range(len(segments)):
			word, countstr = segments[i]
			if word == "COUNT":
				if (i < len(segments) - 1) and (segments[i + 1][0] == "AS"):
					self.counts.append(Count(self.store, countstr, segments[i + 1][1].strip(), quotes))
		self.counts = [count_ for count_ in self.counts if (count_.selects or count_.object_ids)]
		
		# find sums
		for i in range(len(segments)):
			word, sumstr = segments[i]
			if word == "SUM":
				if (i < len(segments) - 1) and (segments[i + 1][0] == "AS"):
					self.sums.append(Sum(self.store, sumstr, segments[i + 1][1].strip(), quotes))
		self.sums = [sum_ for sum_ in self.sums if sum_.select]
		
		# attempt to find shortest relation between all classes (except within classes), if it is not explicitly specified in the RELATED segment
		def find_connection(cls1, cls2, connection = [], done = None):
			
			if done is None:
				done = set()
			if cls1 == cls2:
				return []
			if (cls1, cls2) in done:
				return []
			done.add((cls1, cls2))
			for rel in self.store.classes[cls1].relations:
				for cls3 in self.store.classes[cls1].relations[rel]:
					if cls3 == cls2:
						return connection + [[cls1, rel, cls2]]
			for rel in self.store.classes[cls1].relations:
				for cls3 in self.store.classes[cls1].relations[rel]:
					return find_connection(cls3, cls2, connection + [[cls1, rel, cls3]], done)
			return []
		
		if (len(self.selects) > 1) or self.conditions or self.counts or self.sums:
			relations_done = set()
			for related in self.relations:
				for cls1 in related.classes1:
					for cls2 in related.classes2:
						relations_done.add((cls1, cls2))
			classes = set()
			for select in self.selects:
				classes.update(select.classes)
			for condition in self.conditions:
				classes.update(condition.classes)
			for count_ in self.counts:
				classes.update(count_.classes)
			for sum_ in self.sums:
				classes.update(sum_.classes)
			for cls1 in classes:
				if cls1 == "!*":
					continue
				for cls2 in classes:
					if cls2 == "!*":
						continue
					if cls2 == cls1:
						continue
					if (cls1, cls2) in relations_done:
						continue
					connection = find_connection(cls1, cls2)
					for clsA, rel, clsB in connection:
						if rel.startswith("~"):
							clsA, rel, clsB = clsB, rel[1:], clsA
						if (clsA, clsB) in relations_done:
							continue
						self.relations.append(Related(self.store, "%s.%s.%s" % (clsA, rel, clsB), {}))
						relations_done.add((clsA, clsB))
		
		# sort relations into chains
		def rel_connects(related1, related2):
			# returns True if related1 and related2 connect
			
			return ((related1.classstr1, related1.index1) in ((related2.classstr1, related2.index1), (related2.classstr2, related2.index2))) or ((related1.classstr2, related1.index2) in ((related2.classstr1, related2.index1), (related2.classstr2, related2.index2)))
		
		def idx_in_selects(related):
			# returns index of related in selects or len(selects) + 1 if not found
			
			for idx, select in enumerate(self.selects):
				if (select.classstr, select.index) in ((related.classstr1, related.index1), (related.classstr2, related.index2)):
					return idx
			return len(self.selects) + 1
		
		if self.relations:
			
			neighbours = {}
			for i1, related1 in enumerate(self.relations):
				neighbours[i1] = []
				for i2, related2 in enumerate(self.relations):
					if (i1 == i2) or rel_connects(related1, related2):
						neighbours[i1].append(i2)
			
			chains = []  # [[Related, ...], ...]
			done = set()
			for i in neighbours:
				if i not in done:
					todo = [i]
					chain = []
					while todo:
						i1 = todo.pop()
						for i2 in neighbours[i1]:
							if i2 not in done:
								todo.append(i2)
								done.add(i2)
								chain.append(i2)
					
					if chain:
						# order chain so the classstr mentioned first in selects is first and every relation is connected to one of the previous relations
						i0 = -1
						idx_min = len(self.selects) + 1
						for i1 in chain:
							idx = idx_in_selects(self.relations[chain[i1]])
							if idx < idx_min:
								idx_min = idx
								i0 = i1
						collect = [chain[i0]]
						while len(collect) < len(chain):
							found = False
							for i1 in chain:
								if i1 in collect:
									continue
								for i2 in collect:
									if i1 in neighbours[i2]:
										collect.append(i1)
										found = True
										break
							if not found:
								break
						chains.append([self.relations[i1] for i1 in collect])
			
			self.relations = chains

