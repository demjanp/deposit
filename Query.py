'''
	Deposit Query
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	Interface to a Deposit Store
	Query strings consist of:
	traverses
		obj(id) = Object ID (e.g. obj(1))
		C = Class (Object - Member - Class)
		R = Relation (Object - Relation - Object)
		D = Descriptor (Object - Relation - Class)
		Formed by chaining C, R, D (C, C.D, C.R.*, C.R.C, C.R.C.D, C.R.C.D, C.R.C...R.C.D)
			e.g.: "Class 1.rel 1.Class 2" gets Objects of Class 1 connected to Objects of Class 2 by a Relation labeled "rel 1"
		Class can be replaced with an Object ID (obj(id), obj(id).D, obj(id).R.*, ...)
			e.g.: "obj(1).rel 1.Class 2" gets Objects of Class 2 connected to Object ID 1 by a Relation labeled "rel 1"
			e.g.: "Class 2.~rel 1.obj(1)" gets the same result
		Classless objects can be specified as !*
			e.g.: "!*" gets all classless objects
			e.g.: "!*.*" gets all classless objects with Descriptors
			e.g.: "Class 1.rel 1.!*" gets objects of Class 1 related by rel 1 to classless objects
		Parent Class can be used instead of child Class
			e.g.: Class 1 and Class 2 are members of Class 3; "Class3" will yield Objects of both Class 1 and Class 2
		Wildcard (*) symbol can be used instead of C, R or D elements
			e.g.: "*" to get all Objects
			e.g.: "*.*" to get all Objects with Descriptors
			e.g.: "*.*.Class 1" to get Objects from any Class connected to to Class 1 by any Relation
			e.g.: "Class 1.*.Class 2" to get Objects from Class 1 connected by any Relation to Objects from Class 2
		Objects which are not Members of a Class can be specified using !C
			e.g. "!Class 1"
		Objects without a specific Descriptor can be specified using !D
			e.g. "Class 1.!Class 2"
		Absence of a relation can be specified using !R
			e.g. "Class 2.!rel 1.Class 1"
		Reverse relation can be specified by using ~R (can be combined with ! as !~R)
			e.g. "Class 2.~rel 1.Class 1"
		Use indexing to specify different objects of the same class
			e.g. "Class1#1.rel1.Class1#2.Descr1"
	Values: 1.23, [1, 2, 3], "abc", ...
	Operators:
		standard Python OPERATORS
		e.g.: +, -, *, /, <, >, ==, and, or, ...
	String methods:
		standard Python string methods, e.g.: startswith, upper
	String slices:
		standard Python string slicing, e.g.: "abc"[1] yields "b"
	Quantifiers:
		#(alias, Class, query)
		#(alias, Class, query, Descriptor)
		For every Object in the specified Class (can be * or !*), count number of Objects which satisfy the query
		If Descriptor is specified, instead of counting, sum values of the Descriptor
		In query, obj() must be specified to indicate the parent Object of the quantification
		#(alias) can be used as a reference to the quantifier within the query
		e.g.: #(alias, Class 1, Class 2.Rel 1.obj(), Descr 1)
		e.g.: #(alias, Class 1, Class 2.Rel 1.obj() and Class 2.Descr 1 == 3)
'''

from deposit.DLabel import (DLabel, DString, DResource, DGeometry, DNone, try_numeric, id_to_int, id_to_name)
from numbers import Number
import numpy as np

OPERATORS_TESTS = ["in", "not", "==", "<", ">", "<=", ">=", "!="]
OPERATORS_BOOL = ["and", "or"]
OPERATORS = ["**", "*", "/", "%", "//", "+", "-"] + OPERATORS_TESTS + OPERATORS_BOOL
STRING_METHODS = [method for method in dir("") if not method.startswith("__")] # all string methods

class Query(object):
	# iterate over rows:
	#	Query[id_obj] = {id_cls: value, #alias: value, ...}
	
	def __init__(self, store, query, relation = None, cls_id = None):
		# relation = [obj_id, rel_label, cls_label, cls_id, reversed]
		
		self._store = store
		self._query = query
		self._relation = relation
		self._cls_id = cls_id
		self._columns = None # [[id_cls, label], ["#alias", alias], ...]
		self._objects = None # [id_obj, ...]
		self._data = None # {id_obj: {id_cls: value, #alias: value, ...}, ...}
		self._pos = 0
		self._last_changed = None
	
	@property
	def store(self):
		# Deposit Store
		
		return self._store

	@property
	def query(self):
		# query string
		
		return self._query

	@property
	def columns(self):
		# [[id_cls, label], [#, alias], ...]; classes or aliases representing columns
		
		self._load_data()
		return self._columns

	@property
	def objects(self):
		# [id_obj, ...]
		
		self._load_data()
		return self._objects
	
	def _load_data(self):
		
		if (self._data is None) or (self._last_changed is None) or (self._last_changed < self._store.get_changed()):
			if self._relation:
				self._columns, self._objects, self._data = self._process_relation()
			elif self._cls_id:
				self._columns, self._objects, self._data = self._process_class()
			else:
				self._columns, self._objects, self._data = self._process(self._query)
			self._last_changed = self._store.get_changed()
	
	def keys(self):
		# return [id_obj, ...]
		
		return self.objects

	def values(self):
		# return [{id_cls: value, #alias: value, ...}, ...]; values are of type DLabel
		
		self._load_data()
		return [self._data[id_obj] for id_obj in self._objects]
	
	def items(self):
		# return [(id_obj, {id_cls: value, #alias: value, ...}), ...]
		
		self._load_data()
		return [(id_obj, self._data[id_obj]) for id_obj in self._objects]
	
	def reload(self):
		
		self._data = None
		self._pos = 0
	
	def __getitem__(self, i):
		
		self._load_data()
		if isinstance(i, str):
			return self._data[i]
		elif isinstance(i, int):
			return self._objects[i]
		raise IndexError()
	
	def __iter__(self):
		
		return self
	
	def __next__(self):
		
		self._load_data()
		if self._pos < len(self._objects):
			self._pos += 1
			return self._objects[self._pos - 1]
		else:
			raise StopIteration()
	
	def _process(self, query, quantifying = None):
		# return [columns, objects, data]
		# columns: [[id_cls, label], ["#alias", alias], ...]
		# objects: [id_obj, ...]
		# data: {id_obj: {id_cls: value, #alias: value, ...}, ...}
		
		def _get_fragments(query):
			# split query into fragments
			
			fragments = []
			quantifiers = {} # {alias: [traverse, use_sum], ...}; use_sum = 1/0, sum last Descriptor provided in traverse
			aliases = []
			query = query.strip() # strip whitespace
			i = 0
			collect = ""
			while i < len(query):
				found = ""
				
				space_sepparated = query[i:].lower().split(" ")[0]
				prev = None
				if i > 0:
					prev = query[i - 1]
				if (space_sepparated in OPERATORS) and (not prev in [".", "!"]) and ((not space_sepparated.isalpha()) or prev == " "):
					found = space_sepparated
					i += len(space_sepparated)
				elif space_sepparated.startswith("-") and space_sepparated[1:].isalpha():
					found = space_sepparated[0]
				
				elif query[i:].startswith("obj(") and ((i == 0) or (query[i - 1] in [" ","."])):
					j = query.find(")", i)
					collect += query[i:j+1]
					i = j
				
				elif query[i] in "'\"": # do not modify anything in single or double quotes
					quot_char = query[i]
					j = i + 1
					while query[j] != quot_char:
						j += 1
#					found = query[i:j + 1]
					collect += query[i:j + 1]
					i = j
				
				elif query[i:][:2] == "#(":
					found_brackets = 1
					i += 2
					j = i
					while found_brackets and (j < len(query)):
						if query[j] == "(":
							found_brackets += 1
						elif query[j] == ")":
							found_brackets -= 1
						j += 1
					cont = query[i:j - 1]
					i = j
					j = cont.find(",")
					k = cont.find(",", j + 1)
					l = cont.rfind(",")
					if j == -1:
						# #(alias)
						found = ["#", "#%s" % cont.strip(), None]
					else:
						alias = "#%s" % cont[:j].strip()
						if (l != k) and (not True in [(c in "[]") for c in cont[l + 1:].strip()]):
							# #(alias, Class, query, Descriptor)
							quantifiers[alias] = [cont[j + 1:k].strip(), cont[k + 1:l].strip(), cont[l + 1:].strip()]
						else:
							# #(alias, Class, query)
							quantifiers[alias] = [cont[j + 1:k].strip(), cont[k + 1:].strip(), None]
						aliases.append(alias)
						found = ["#", alias, None]
				
				elif query[i] == "[":
					j = i
					while (query[j] != "]") and (j < len(query)):
						j += 1
					if query[j] == "]":
						found = query[i:j+1]
						i = j
				elif query[i] in "()":
					if query[i:i+2] == "()":
						collect += query[i:i+2].strip()
						i += 2
					else:
						found = query[i]
				else:
					if query[i]:
						collect += query[i]
				
				if found:
					if collect.strip():
						fragments.append(collect)
						collect = ""
					fragments.append(found)
				i += 1
			if collect.strip():
				fragments.append(collect)

			# remove stand-alone quantifier definitions from fragments
			collect = []
			for i in range(len(fragments)):
				if isinstance(fragments[i], list) and (fragments[i][0] == "#"):
					if ((i > 0) and (fragments[i - 1] in OPERATORS)) or ((i < len(fragments) - 1) and (fragments[i + 1] in OPERATORS)):
						collect.append(fragments[i])
				else:
					collect.append(fragments[i])
			fragments = collect
			
			return fragments, quantifiers, aliases
		
		def _get_all_classes(label):
				# collect class id + ids of all its subclasses
				
				classes = np.array([])
				id_cls = self._store.queryfnc.get_class_by_label(label)
				if not id_cls is None:
					classes = np.union1d(classes, np.r_[self._store.members.get_all_subclasses(id_cls), [id_cls]])
				return classes.tolist()

		def _get_cls_alias(cls):
			
			alias = cls.split("#")
			if len(alias) > 1:
				return alias[1]
			return None
			
		def _get_cls(cls):
			
			c = cls.count("#")
			if c == 2:
				return "#".join(cls.split("#")[:2])
			elif c:
				return cls.split("#")[0]
			return cls
			
		def _proc_chain(elements):
			
			elements = elements[::-1]
			
			# process first element
			element = elements.pop()
			objects = np.array([])
			cls = None
			if element == "*": # Objects of any Class
				objects = self._store.objects.get() # [id_obj, ...]
			elif element == "!*": # classless Objects
				objects = self._store.objects.get_classless() # [id_obj, ...]
			elif element.startswith("obj("): # Object specified by id
				if "#" in element:
					objects = np.array([element[3:].strip("()")], dtype = object)
				else:
					objects = np.array(["_".join([self._store.get_dep_class_prefix("Object"), element[3:].strip("()")])], dtype = object)
			else:# Objects specified by Class
				objects = []
				cls = element.strip("!")
				alias = _get_cls_alias(cls)
				for id_cls in _get_all_classes(_get_cls(cls)):
					objects += [id_obj for id_obj in self._store.members.get(id_cls)]
				objects = np.unique(objects)
				if element.startswith("!"):
					# Objects are not Members of Class
					objects = np.setdiff1d(self._store.objects.get(), objects)
			
			if (not elements) or (not objects.shape[0]):
				return objects
			
			# process rest of the chain
			first_class = True
			objects = objects.reshape((-1,1))
			while elements and objects.shape[0]:
				
				if len(elements) == 1: # collected Objects with a Descriptor
					descr = elements.pop()
					neg_descr = descr.startswith("!")
					descr = descr.strip("!")
					objects2 = [] # [[id_obj0, id_cls, id_rel, read_only], ...]
					id_cls = self._store.queryfnc.get_class_by_label(descr)
					if not id_cls is None:
						if not cls is None:
							id_cls0 = self._store.queryfnc.get_class_by_label(_get_cls(cls))
							if alias:
								id_cls0 += "#" + alias
						cls_all = _get_all_classes(descr)
						if cls_all:
							res = self._store.queryfnc.get_object_descriptors(objects[:,-1], cls_all, neg_descr) # [[id_obj2, id_rel, id_cls], ...]
							if res.size:
								for i in range(objects.shape[0]):
									slice = res[res[:,0] == objects[i,-1]]
									if slice.size:
										id_rel, id_cls2 = slice[0,1:]
										if cls is None:
											objects2.append([objects[i,0], id_cls2, id_rel, not first_class])
										else:
											objects2.append([objects[i,0], ".".join([id_cls0, id_cls2]), id_rel, not first_class])
					objects = np.array(objects2, dtype = object)
				
				else: # R.C pair -> Objects of Class related by Relation to collected Objects
					first_class = False
					rel = elements.pop()
					cls = elements.pop()
					neg_rel = rel.startswith("!")
					rel = rel.strip("!")
					rev = rel.startswith("~")
					rel = rel.strip("~")
					if cls.startswith("obj("): # Object specified by id
						if "#" in cls:
							id_obj = cls[3:].strip("()")
						else:
							id_obj = "_".join([self._store.get_dep_class_prefix("Object"), cls[3:].strip("()")])
						objects2 = self._store.queryfnc.is_related(objects[:,-1], None if (rel == "*") else rel, np.array([id_obj]), rev, neg_rel)
					elif cls == "!*": # classless Objects
						objects2 = self._store.queryfnc.get_related_classless(objects[:,-1], None if (rel == "*") else rel, rev, neg_rel)
					else: # Objects specified by Class
						neg_cls = cls.startswith("!")
						cls = cls.strip("!")
						alias = _get_cls_alias(cls)
						if cls != "*":
							classes = _get_all_classes(_get_cls(cls))
						objects2 = self._store.queryfnc.get_related(objects[:,-1], None if (rel == "*") else rel, None if (cls == "*") else classes, rev, neg_rel, neg_cls)
					if objects.shape[1] == 1:
						objects = objects2.copy()
					elif objects.size and objects2.size:
						collect = []
						for row in objects:
							slice = objects2[objects2[:,0] == row[-1]]
							if slice.size:
								for id_obj2 in np.unique(slice[:,1]):
									collect.append(row.tolist() + [id_obj2])
						objects = np.array(collect, dtype = object)
					else:
						objects = np.array([])
				
			if objects.shape[0]:
				if objects.shape[1] == 1:
					objects = np.unique(objects.flatten())
				elif self._store.get_dep_class_by_id(objects[0,1]) == "Object":
					objects = np.unique(objects[:,0])
				else:
					objects = objects.astype(str)
					objects = np.unique(np.ascontiguousarray(objects).view(np.dtype((np.void, objects.dtype.itemsize * objects.shape[1])))).view(objects.dtype).reshape(-1, objects.shape[1])
					objects = objects.astype(object)
			
			return objects # [id_obj, ...] or [[id_obj, id_cls, id_rel, read_only], ...]
		
		def _proc_quantifiers(quantifiers):
			# quantifiers: {alias: [cls, query, descr], ...}; use_sum = 1/0, sum last Descriptor provided in traverse
			# into
			# {alias: {obj_id: quantity, ...}, ...}
			
			for alias in quantifiers:
				cls, qry, descr = quantifiers[alias]
				descr_id = None
				if not descr is None:
					descr_id = self._store.queryfnc.get_class_by_label(descr)
					if descr_id is None:
						continue
				
				repl = [] # [i, ...]; indexes to use to replace "obj()" in query
				i = -1
				while True:
					i = qry.find("obj()", i + 1)
					if i == -1:
						break
					if (i > -1) and ((i == 0) or (qry[i - 1] in " .")):
						repl.append(i)
				if not repl:
					continue
				collect = []
				j = 0
				for i in repl:
					if i > 0:
						collect.append(qry[j:i])
					collect.append(None)
					j = i + 5
				if j < len(qry) - 1:
					collect.append(qry[j:])
				qry = collect
				
				collect = {} # {obj_id: quantity, ...}
				cnt = 1
				objects = self._store.members.get(self._store.queryfnc.get_class_by_label(cls), subclasses = True)
				for obj_id in objects:
					if cnt % 10 == 0:
						self._store.message("Quantifying: %s %d/%d" % (cls, cnt, objects.shape[0]))
						print("\rQuantifying: %s %d/%d            " % (cls, cnt, objects.shape[0]), end = "")
					cnt += 1
					query_quan = "".join([(("obj(%s)" % (id_to_name(obj_id))) if (frag is None) else frag) for frag in qry])
					if not descr is None:
						query_quan = "%s and *.%s" % (query_quan, descr)
					res = self._process(query_quan, quantifying = True)
					if descr_id is None:
						collect[obj_id] = res.shape[0]
					elif res.size:
						collect[obj_id] = np.genfromtxt(res[:,np.where(res[0] == descr_id)[0][0] + 1].astype("|S")).sum()
				quantifiers[alias] = collect
		
		def _add_labels(frag_collect):
			# get labels for Objects with labels & apply string methods and slices
			
			i = 0
			while i < len(frag_collect):
				if isinstance(frag_collect[i], np.ndarray) and (frag_collect[i].ndim == 2) and (frag_collect[i].shape[1] % 2 == 0):
					frag_collect[i] = frag_collect[i].astype(object)
					found_string_method = False
					if i < len(frag_collect) - 1:
						if isinstance(frag_collect[i + 1], str) and (frag_collect[i + 1][0] == "."):
							# string method after
							labels = self._store.get_label(frag_collect[i][:,2], frag_collect[i][:,3], as_string = True)
							frag_collect[i] = frag_collect[i][[eval("\"%s\"%s" % (labels[j], frag_collect[i + 1])) for j in range(len(labels))]]
							del frag_collect[i + 1]
						else:
							# check for after
							slice = None
							slice_min = 0
							if isinstance(frag_collect[i + 1], str) and (frag_collect[i + 1][0] == "["):
								j = 0
								while (frag_collect[i + 1][j] != "]") and (j < len(frag_collect[i + 1])):
									j += 1
								if frag_collect[i + 1][j] == "]":
									slice_txt = frag_collect[i + 1][1:j]
									if ":" in slice_txt:
										slice_txt = slice_txt.split(":")
										slice = []
										for val in slice_txt[:2]:
											try:
												val = int(val)
											except:
												val = None
											slice.append(val)
										if slice == [None, None]:
											slice = None
										if not slice[0] is None:
											slice_min = slice[0]
									else:
										try:
											slice = [int(slice_txt)]
											slice_min = slice[0]
										except:
											pass
							if not slice is None:
								# string slice after
								labels = self._store.get_label(frag_collect[i][:,2], frag_collect[i][:,3])
								for j, id_rel in enumerate(frag_collect[i][:,2]):
									if isinstance(labels[j], DString) and isinstance(labels[j].working, str) and (len(labels[j].working) > slice_min):
										if (len(slice) == 1) and (not slice[0] is None):
											labels[j].set_working(labels[j].working[slice[0]])
										elif (not slice[0] is None) and (not slice[1] is None):
											labels[j].set_working(labels[j].working[slice[0]:slice[1]])
										elif slice[0] is None:
											labels[j].set_working(labels[j].working[:slice[1]])
										elif slice[1] is None:
											labels[j].set_working(labels[j].working[slice[0]:])
										frag_collect[i][j,2] = labels[j]
										frag_collect[i] = frag_collect[i][:,:-1]
									else:
										frag_collect[i][j,2] = DNone()
										frag_collect[i] = frag_collect[i][:,:-1]
								del frag_collect[i + 1]
								found_string_method = True
					if not found_string_method:
						frag_collect[i][:,2] = self._store.get_label(frag_collect[i][:,2], frag_collect[i][:,3])
						frag_collect[i] = frag_collect[i][:,:-1]
				i += 1
		
		def _eval_operators(frag_collect):
			# evaluate OPERATORS
			
			def _as_value(val):
				
				if isinstance(val, DLabel):
					return val.working
				return val
			
			def _add_working_column(vals):
				# check if values have a working column, and if not add it if possible
				
				if vals.shape[1] % 2 == 1:
					if vals.shape[1] == 3:
						return np.vstack((vals.T, vals[:,vals.shape[1] - 1])).T
					else:
						# working column is not present & cannot apply operator on more than one column
						return None
				return vals
			
			def _eval_value(val1, val2, op, l_to_r, is_num):
				if l_to_r:
					evstr = ("try_numeric(val1) %s val2" if is_num else "val1 %s val2")
					if not is_num:
						val2 = val2.strip("'\"")
				else:
					evstr = ("val2 %s try_numeric(val1)" if is_num else "val2 %s val1")
					if not is_num:
						val1 = val1.strip("'\"")
				try:
					return eval(evstr % (op), {"val1": val1, "val2": val2, "try_numeric": try_numeric})
				except:
					return ""
			
			def _eval_operator(val, op):
				
				try:
					return eval("%s val" % (op), {"val": try_numeric(val)})
				except:
					return ""
			
			def _eval_arrays(val1, val2, op):
				
				try:
					return eval("val1 %s val2" % (op), {"val1": try_numeric(val1), "val2": try_numeric(val2)})
				except:
					return ""
			
			def _eval_quan_binary(id_obj, alias, expr):
				
				q = quantifiers[alias][id_obj]
				if not expr is None:
					try:
						return eval(expr % "val", {"val": q}) != 0
					except:
						return False
				return q != 0
			
			def _O_OP_O(vals, op):
				# perform and / or combination of lists
				
				if op in OPERATORS_BOOL:
					if op == "and":
						return np.intersect1d(vals[0], vals[1])
					return np.union1d(vals[0], vals[1])
				return False
			
			def _OL_OP_OL(vals, op, is_n, is_np):
				# merge both lists to one with labels combined by operator
				
				for v in range(2):
					if is_n[v]:
						vals[v] = vals[v].reshape((-1,1))
					elif (not op in OPERATORS_BOOL) and (vals[v].shape[1] % 2 == 1) and (vals[v].shape[1] != 3):
						# list has no working column and more than one descriptor - cannot perform non-boolean operations on multiple values
						return False
				
				result = np.array([])
				if op == "or":
					result = np.union1d(vals[0][:,0], vals[1][:,0])
				else: # and & other OPERATORS
					result = np.intersect1d(vals[0][:,0], vals[1][:,0])
				
				if not result.shape[0]:
					return result
				
				working = None
				# filter only Objects present in result
				vals[0] = vals[0][np.in1d(vals[0][:,0], result)]
				vals[1] = vals[1][np.in1d(vals[1][:,0], result)]
				
				idxs = np.argsort(result)
				result = result[idxs]
				
				if op == "or":
					# vals arrays can have different lengths
					for v in range(2):
						if is_n[v]:
							vals[v] = result.copy()
						else:
							mask = np.in1d(result, vals[v][:,0])
							vals_new = np.tile(vals[v][0], result.shape[0]).reshape((result.shape[0], -1)).astype(object)
							rows = mask.shape[0] - mask.sum()
							cols = vals[v][0][::2].shape[0]
							vals_new[~mask,::2] = np.repeat(np.array([DNone()], dtype = object), rows * cols).reshape((rows, cols))
							vals_new[mask] = vals[v]
							vals_new[:,0] = result
							vals[v] = vals_new.copy()
				else:
					for v in range(2):
						if vals[v].shape[0]:
							if vals[v].shape[0] == result.shape[0]:
								vals[v] = vals[v][idxs]
							else:
								vals[v] = vals[v][np.argsort(vals[v][:,0])]
					vals_len = max(vals[0].shape[0], vals[1].shape[0])
					if vals_len > result.shape[0]:
						v = 0 if (vals[0].shape[0] > result.shape[0]) else 1
						vals2 = np.zeros((vals[v].shape[0], vals[not v].shape[1])).astype(object)
						vals2[:,0] = vals[v][:,0]
						for row in vals[not v]:
							mask = (vals2[:,0] == row[0])
							vals2[mask] = np.tile(row, mask.sum()).reshape((-1,row.shape[0]))
						vals[not v] = vals2
						result = vals[v][:,0]
				
				if not op in OPERATORS_BOOL:
					# further filter list by working values & operator
					# result, vals[0], vals[1] have identical Object ids in the first column
					working = np.array([_eval_arrays(_as_value(vals[0][l,-1]), _as_value(vals[1][l,-1]), op) for l in range(vals[0].shape[0])], dtype = object)
					
					if op in OPERATORS_TESTS:
						mask = (working == True)
					else:
						mask = (working != "")
					result = result[mask]
					vals[0] = vals[0][mask]
					vals[1] = vals[1][mask]
					working = working[mask]
				
				if not result.shape[0]:
					return result
				
				# merge classes & labels from both lists
				if is_n.any():
					v = np.where(is_np)[0][0]
					class_ids = vals[v][0][1:-1][::2] if (vals[v].shape[1] % 2 == 0) else vals[v][0][1:][::2]
				else:
					class_ids = np.union1d(*[(vals[v][0][1:-1][::2] if (vals[v].shape[1] % 2 == 0) else vals[v][0][1:][::2]) for v in range(2)])
				# remove working column from vals
				for v in range(2):
					if is_n[v]:
						vals[v] = vals[v].reshape((-1,1))
					elif vals[v].shape[1] % 2 == 0:
						vals[v] = vals[v][:,:-1]
				result = np.hstack([result.reshape((-1,1))] + [vals[v][:,1:] for v in range(2) if vals[v].shape[0]])
				
				if not working is None:
					# add working values as last column
					result = np.hstack((result, working.reshape((-1,1))))
				
				return result
			
			def _O_OP_Q(vals, op, is_n):
				# calculate quantity for every Object in list and filter labels in list by operator and quantity
				
				if op in OPERATORS_BOOL:
					if is_n[0]:
						result = vals[0]
						alias, expr = vals[1][1:]
					else:
						result = vals[1]
						alias, expr = vals[0][1:]
					return result[np.array([_eval_quan_binary(id_obj, alias, expr) for id_obj in result], dtype = bool)]
				return False
			
			def _O_OP_V(vals, op, is_n):
				# and: keep list of Objects if value evaluates as true
				# or: keep value if list is empty else keep list
				# if or: keep list of Objects, if and: keep list of Objects if value evaluates as true
				
				if op in OPERATORS_BOOL:
					if is_n[0]:
						result = vals[0]
						val = vals[1]
					else:
						result = vals[1]
						val = vals[0]
					if op == "and":
						return result if eval("val", {"val": val}) else False
					elif not result.shape[0]:
						return val
				return False
			
			def _OL_OP_Q(vals, op, is_np):
				# calculate quantity for every Object in list and modify labels in list by operator and quantity
				
				if is_np[0]:
					result = vals[0].copy()
					alias, expr = vals[1][1:]
				else:
					result = vals[1].copy()
					alias, expr = vals[0][1:]
				
				result = _add_working_column(result)
				if result is None:
					return False
				
				val_col = result.shape[1] - 1
				result[:,val_col] = [_eval_value(_as_value(val1), quantifiers[alias][id_obj], op, is_np[0], True) for id_obj, val1 in result[:,[0,val_col]]]
				
				if op in OPERATORS_TESTS:
					return result[result[:,val_col] == True,:val_col]
				return result[result[:,val_col] != ""]
			
			def _OL_OP_V(vals, op, is_np):
				# modify labels in list by operator and value
				
				if is_np[0]:
					result = vals[0].copy()
				else:
					result = vals[1].copy()
				
				result = _add_working_column(result)
				if result is None:
					return False
				
				val_col = result.shape[1] - 1
				val2 = vals[1 if is_np[0] else 0]
				if not isinstance(val2, bool):
					val2 = try_numeric(val2)
				is_num = isinstance(val2, Number)
				result[:,val_col] = [_eval_value(_as_value(val1), val2, op, is_np[0], is_num) for val1 in result[:,val_col]]
				if op in (OPERATORS_TESTS + OPERATORS_BOOL):
					return result[result[:,val_col] == True,:val_col]
				return result[result[:,val_col] != ""]
			
			def _Q_OP_V(vals, op, is_quan):
				# modify quantifier fragment by adding operator and value as extra parameter to be evaluated when quantifying
				
				if is_quan[0]:
					result = vals[0]
				else:
					result = vals[1]
				expr = "%s" if (result[2] is None) else "(%s)" % result[2]
				val1, val2 = (expr, vals[1]) if is_quan[0] else (vals[0], expr)
				result[2] = "%s %s %s" % (val1, op, val2)
				return result
			
			def _V_OP_V(vals, op):
				# evaluate expression
				
				try:
					return eval("val0 %s val1" % (op), {"val0": vals[0], "val1": vals[1]})
				except:
					return False
			
			def _OP_OL(vals, op):
				# modify labels in list by operator
				
				result = _add_working_column(vals[1].copy())
				if result is None:
					return False
				
				val_col = result.shape[1] - 1
				result[:,val_col] = [_eval_operator(_as_value(val), op) for val in result[:,val_col]]
				return result[result[:,val_col] != ""]
			
			def _OP_Q(vals, op):
				# modify quantifier fragment by adding operator as extra parameter to be evaluated when quantifying
				
				result = vals[1]
				expr = "%s" if (result[2] is None) else "(%s)" % result[2]
				result[2] = "%s %s" % (op, expr)
				return result
			
			def _OP_V(vals, op):
				# modify value by operator
				
				try:
					return eval("%s val" % (op), {"val1": vals[1]})
				except:
					return False
			
			frag_collect = ["("] + frag_collect + [")"]
			found = True
			while (len(frag_collect) > 1) and found:
				# find a sequence in parentheses
				deleted = True
				while deleted:
					deleted = False
					j = 0
					while (not (isinstance(frag_collect[j], str) and (frag_collect[j] == ")"))) and (j < len(frag_collect) - 1):
						j += 1
					i = j - 1
					while (not (isinstance(frag_collect[i], str) and (frag_collect[i] == "("))) and (i > 0):
						i -= 1
					if j - i == 2:
						if isinstance(frag_collect[i + 1], np.ndarray) and not frag_collect[i + 1].shape[0]:
							frag_collect[i + 1] = False
						del frag_collect[j]
						del frag_collect[i]
						deleted = True
				# find OPERATORS
				idxs = [] # [[idx, order], ...]; idx = index in frag_collect; order = order of precedence (0 = first)
				for k in range(i + 1, j):
					if isinstance(frag_collect[k], str) and (frag_collect[k] in OPERATORS):
						idxs.append([k, OPERATORS.index(frag_collect[k])])
				if idxs:
					# evaluate expressions by order of precedence of OPERATORS
					idxs = np.array(sorted(idxs, key = lambda row: row[1]), dtype = int)[:,0]
					while idxs.shape[0] and found:
						found = False
						for ki in range(idxs.shape[0]):
							k = idxs[ki]
							op = frag_collect[k]
							vals = []
							vals.append(frag_collect[k - 1] if (k > i + 1) else None)
							vals.append(frag_collect[k + 1] if (k < j - 1) else None)
							is_n = np.array([(isinstance(val, np.ndarray) and (val.ndim == 1)) for val in vals])
							is_np = np.array([(isinstance(val, np.ndarray) and (val.ndim == 2)) for val in vals])
							is_quan = np.array([isinstance(val, list) for val in vals])
							for v in range(2):
								if isinstance(vals[v], str) and (vals[v] in OPERATORS):
									vals[v] = None
							to_del = 0
							result = None
							
							# O: Objects; OL: Objects with labels; Q: quantifier; V: value; OP: operator
							
							# O OP O
							if is_n.all(): # both values are lists of Objects
								result = _O_OP_O(vals, op)
								found = True
								to_del = 2

							# OL OP OL / O OP OL / OL OP O
							elif is_np.all() or (is_n.any() and is_np.any()): # both values are lists of Objects, at least one with labels
								
								result = _OL_OP_OL(vals, op, is_n, is_np)
								found = True
								to_del = 2
							
							# O OP Q / Q OP O
							elif is_n.any() and is_quan.any(): # list of Objects and a quantifier
								result = _O_OP_Q(vals, op, is_n)
								found = True
								to_del = 2
							
							# O OP V / V OP O
							elif is_n.any() and (not vals[0] is None) and (not vals[1] is None): # list of Objects and a value
								result = _O_OP_V(vals, op, is_n)
								found = True
								to_del = 2
							
							# OL OP Q / Q OP OL
							elif is_np.any() and is_quan.any(): # quantifier and a list of Objects with labels
								# calculate quantity for every Object in list and modify labels in list by operator and quantity
								result = _OL_OP_Q(vals, op, is_np)
								found = True
								to_del = 2
							
							# OL OP V / V OP OL
							elif is_np.any() and (not vals[0] is None) and (not vals[1] is None) and (not is_quan.any()): # value and a list of Objects with labels
								# modify labels in list by operator and value
								result = _OL_OP_V(vals, op, is_np)
								found = True
								to_del = 2
							
							# Q OP Q
							elif is_quan.all(): # two quantifiers
								# evaluate each quantifier for each Object from first Class of its fragment then handle as OL OP OL
								for v in range(2):
									pass # DEBUG
								found = True
							
							# Q OP V / V OP Q
							elif is_quan.any() and (not vals[0] is None) and (not vals[1] is None): # value and quantifier
								# modify quantifier fragment by adding operator and value as extra parameter to be evaluated when quantifying
								result = _Q_OP_V(vals, op, is_quan)
								found = True
								to_del = 2
							
							# V OP V
							elif (not is_np.any()) and (not is_quan.any()) and (not vals[0] is None) and (not vals[1] is None): # two values
								result = _V_OP_V(vals, op)
								found = True
								to_del = 2
							
							# OP OL
							elif is_np[1] and (vals[0] is None): # operator and a list of Objects with labels
								result = _OP_OL(vals, op)
								found = True
								to_del = 1
							
							# OP Q
							elif is_quan[1] and (vals[0] is None): # operator and a quantifier
								result = _OP_Q(vals, op)
								found = True
								to_del = 1
							
							# OP V
							elif (not is_np[1]) and (not is_quan[1]) and (vals[0] is None) and (not vals[1] is None): # operator and a value
								result = _OP_V(vals, op)
								found = True
								to_del = 1
							
							if isinstance(result, np.ndarray) and not result.shape[0]:
								result = False
							
							if to_del == 2:
								del frag_collect[k:k + 2]
								idxs[idxs >= k] -= 2
								frag_collect[k - 1] = result
							elif to_del == 1:
								del frag_collect[k]
								idxs[idxs >= k] -= 1
								frag_collect[k] = result
						
						idxs = idxs[(idxs > i + 1) & (idxs < len(frag_collect))]
				else:
					found = False
			return frag_collect
		
		def _objects_to_dicts(objects):
			# convert [[id_obj, id_cls1, label1, id_cls2, label2, #alias, value, ...], ...]
			# 	or [id_obj, ...]
			# 	to [columns, objects, data]
			# id_cls1... = id_cls -> Descriptor id or Name.id_cls -> Class name.Descriptor id
			# columns: [[id_cls, label], ["#alias", alias], ...]
			# objects: [id_obj, ...]
			# data: {id_obj: {id_cls: value, #alias: value, ...}, ...}
			
			def _descr_id_to_label(id):
				
				if id.startswith("#"):
					return DString(id, read_only = True)
				split = False
				if ("#" in id) and ("." in id):
					i = id.find(".", id.find("#"))
					id_cls, id_descr = id[:i], id[i + 1:]
					split = True
				elif "." in id:
					id_cls, id_descr = id.split(".")
					split = True
				if split:
					alias = _get_cls_alias(id_cls)
					cls_label = self._store.get_label(_get_cls(id_cls), as_string = True)
					if alias:
						cls_label = "%s#%s" % (cls_label, alias)
					return DString(".".join([cls_label, self._store.get_label(id_descr, as_string = True)]), read_only = True)
				return self._store.get_label(id, read_only = True)
			
			def _descr_order(id):
				
				if id.startswith("#"):
					return -1
				split = False
				'''
				cls_1.descr_2
				cls_1#1.descr_2
				iden.ti.fier#cls_1.iden.ti.fier#descr_2
				iden.ti.fier#cls_1#1.iden.ti.fier#descr_2
				'''
				if ("#" in id) and ("." in id):
					i = id.find(".", id.find("#"))
					id_cls, id_descr = id[:i], id[i + 1:]
					split = True
				elif "." in id:
					id_cls, id_descr = id.split(".")
					split = True
				if split:
					return max(self._store.get_order(_get_cls(id_cls)), self._store.get_order(id_descr))
				return self._store.get_order(id)
			
			if objects is None:
				return [], [], {}
			data = {}
			if objects.ndim == 2:
				columns = np.unique(objects[:,1::2]).tolist()
				collect = sorted(objects[:,0].tolist())
				for id_obj in collect:
					slice = objects[objects[:,0] == id_obj]
					data[id_obj] = {}
					for row in slice:
						for i in range(1, objects.shape[1], 2):
							id_cls = row[i]
							if not id_cls in data[id_obj]:
								value = row[i + 1]
								if not isinstance(value, DNone):
									data[id_obj][id_cls] = value if isinstance(value, DLabel) else DString(value)
					for id_cls in columns:
						if not id_cls in data[id_obj]:
							data[id_obj][id_cls] = DNone()
				objects = collect
			else:
				columns = []
				for id_obj in objects:
					data[id_obj] = {}
				objects = objects.tolist()
			
			if columns:
				columns = [[col, _descr_id_to_label(col)] for col in columns]
				columns_order = dict([(row[0], _descr_order(row[0])) for row in columns])
				max_order = max(columns_order.values()) + 1
				columns = sorted(columns, key = lambda row: max_order if row[0].startswith("#") else columns_order[row[0]])
			if objects:
				objects = sorted(np.unique(objects), key = lambda id_obj: id_to_int(id_obj))
			return columns, objects, data
		
		# split query into fragments
		fragments, quantifiers, aliases = _get_fragments(query)
		
		# evaluate fragments
		frag_collect = [] # ["(", ")", operator, string method, quantifier, alias, value, Objects, Objects_Vals, ...]
		# operator:			** * / % // + - in not == < > <= >= != and or
		# string method:	.startswith("s"), .upper(), ...
		# string slice:		[1]
		# quantifier:		["#", alias, Class, query, Descriptor]
		# value:			1.23, [1, 2, 3], "abc", ...
		# Objects:			[id_obj, ...]
		# Objects_Vals:		[[id_obj, id_cls, id_val], ...]
		
		# translate traverses into Objects and Objects_Vals
		i = -1
		while i < len(fragments) - 1:
			i += 1
			
			if isinstance(fragments[i], list):
				frag_collect.append(fragments[i])
				continue
			fragments[i] = fragments[i].strip()
			if (fragments[i][0] in "()") or ((fragments[i] in OPERATORS) and not ((fragments[i] == "*") and (len(fragments) == 1))):
				frag_collect.append(fragments[i])
				continue
			
			# evaluate elements of fragment
			queue = fragments[i].split(".")
			elements = []
			while queue:
				collect = [queue.pop(0)]
				# keep everything within obj() together
				if collect[-1].startswith("obj("):
					while not collect[-1].endswith(")"):
						collect.append(queue.pop(0))
				# keep everything within double-quotes together
				else:
					quotes = collect[-1].count('"') % 2
					while quotes:
						collect.append(queue.pop(0))
						quotes -= collect[-1].count('"') % 2
				elements.append(".".join(collect))
			
			# check if first element is part of a traverse
			is_traverse = False
			if (elements[0] in ["*", "!*"]) or elements[0].startswith("obj("):
				is_traverse = True
			if not is_traverse:
				is_traverse = self._store.queryfnc.class_exists(elements[0].strip("!").split("#")[0])
			if not is_traverse:
				frag_collect.append(fragments[i])
				continue
			
			# if traverse equals C.* or obj(id).* modify subsequent fragments to display all descriptors
			if (len(elements) == 2) and (elements[-1] == "*"):
				cls = elements[0].strip('"')
				collect = []
				if cls.startswith("obj("):
					if "#" in cls:
						id_obj = cls[3:].strip("()")
					else:
						id_obj = "_".join([self._store.get_dep_class_prefix("Object"), cls[3:].strip("()")])
					for _, _, id_cls in self._store.queryfnc.get_object_descriptors([id_obj], None, False):
						collect += ["or", ".".join([cls, self._store.get_label(id_cls, as_string = True)])]
				elif cls == "!*":
					objects = self._store.objects.get_classless()
					res = self._store.queryfnc.get_object_descriptors(objects, None, False) # [[id_obj, id_rel, id_cls], ...]
					if res.size:
						labels = self._store.get_label(res[:,2], as_string = True)
						for j in range(res.shape[0]):
							collect += ["or", ".".join(["obj(%s)" % (id_to_name(res[j,0])), labels[j]])]
				else:
					if cls == "*":
						classes = self._store.classes.get().tolist()
					else:
						classes = _get_all_classes(cls)
					for id_cls1 in classes:
						cls1 = self._store.get_label(id_cls1, as_string = True)
						for id_cls2 in self._store.classes.get_descriptors(id_cls1):
							collect += ["or", ".".join([cls1, self._store.get_label(id_cls2, as_string = True)])]
					if classes and (not collect):
						collect = ["or", cls]
				if collect:
					fragments = fragments[:i] + ["("] + collect[1:] + [")"] + fragments[i + 1:]
					i -= 1
					continue
				
			# check if last element is a built in string method
			string_method = None
			if elements[-1].endswith("()") or ((elements[-1] in STRING_METHODS) and (i < len(fragments) - 1) and fragments[i + 1].startswith("(")):
				string_method = elements.pop()
			
			# process the C.R.C.D chain
			frag_collect.append(_proc_chain(elements)) # [id_obj, ...] or [[id_obj, id_cls, id_rel, read_only], ...]
			
			# collect string methods
			if not string_method is None:
				if string_method.endswith("()"):
					frag_collect.append(".%s" % string_method)
				else:
					collect = [".%s" % string_method, "("]
					i += 1
					found = 1
					while found:
						i += 1
						collect.append(fragments[i])
						if fragments[i] == "(":
							found += 1
						elif fragments[i] == ")":
							found -= 1
					if (len(collect) == 4) and isinstance(try_numeric(collect[2]), Number): # if the format is .function(number), put number in quotes
						collect[2] = "\"%s\"" % collect[1]
					frag_collect.append("".join(collect))
		
		_proc_quantifiers(quantifiers)
		# quantifiers = {alias: {obj_id: quantity, ...}, ...}
		
		# get labels for Objects with labels & apply string methods and slices
		_add_labels(frag_collect)
		
		# evaluate operators
		frag_collect = _eval_operators(frag_collect)
		
		# consolidate results
		if len(frag_collect) == 1:
			if isinstance(frag_collect[0], np.ndarray):
				objects = frag_collect[0]
			else: # some error in evaluation or non-list returned
				objects = None
		else:
			objects = np.array([])
		# objects = [[id_obj, id_cls1, label1, id_cls2, label2, ...]
		
		# strip last column with working labels
		if (not objects is None) and (objects.ndim == 2):
			if objects.shape[1] % 2 == 0:
				objects = objects[:,:-1]
		
		# add quantifiers to result
		if quantifiers:
			if (objects is None) or (not objects.size):
				objects = []
				for alias in quantifiers:
					for obj_id in quantifiers[alias]:
						if not obj_id in objects:
							objects.append(obj_id)
				objects = np.array(objects, dtype = object)
			quan_columns = sorted(quantifiers.keys())
			quan_columns = [(quan_columns[i // 2] if (i % 2 == 0) else None) for i in range(len(quan_columns) * 2)]
			collect = []
			for row in objects:
				if isinstance(row, np.ndarray):
					row = row.tolist() + quan_columns
				else:
					row = [row] + quan_columns
				obj_id = row[0]
				for alias in quantifiers:
					row[row.index(alias) + 1] = quantifiers[alias][obj_id] if (obj_id in quantifiers[alias]) else 0
				collect.append(row)
			objects = np.array(collect, dtype = object)
		# objects = [[id_obj, id_cls1, label1, id_cls2, label2, #alias, value, ...]
		
		if quantifying:
			# return results as 
			return np.array([]) if (objects is None) else objects
		
		# return results as [columns, [id_obj, value, value, ...]]
		return _objects_to_dicts(objects)
	
	def _find_descriptors(self, objects):
		# return [columns, objects, data]
		# columns: [[cls_id, label], ["#alias", alias], ...]
		# objects: [id_obj, ...]
		# data: {id_obj: {cls_id: value, #alias: value, ...}, ...}
		
		data = dict([(obj_id2, {}) for obj_id2 in objects])
		descr_ids = np.array([], dtype = object)
		if self._store._db.relations.size:
			slice = self._store._db.relations[np.in1d(self._store._db.relations[:,2], objects)]
			if slice.size:
				for descr_id, rel_id, obj_id2, label, dtype in slice:
					if descr_id.startswith(self._store.get_dep_class_prefix("Class")):
						descr_ids = np.union1d(descr_ids, [descr_id])
						if not obj_id2 in data:
							data[obj_id2] = {}
						data[obj_id2][descr_id] = globals()[dtype](label, relation = rel_id)
		
		for descr_id in descr_ids:
			for obj_id2 in data:
				if not descr_id in data[obj_id2]:
					data[obj_id2][descr_id] = DNone()
		columns = [[descr_id, DString(self._store.get_label(descr_id, as_string = True), read_only = True)] for descr_id in descr_ids]
		
		if isinstance(objects, np.ndarray):
			objects = objects.tolist()
		if objects:
			objects = sorted(np.unique(objects), key = lambda id_obj: id_to_int(id_obj))
		if columns:
			columns = sorted(columns, key = lambda item: self._store.get_order(item[0]))
		
		return columns, objects, data
	
	def _process_relation(self):
		# return [columns, objects, data]
		# columns: [[cls_id, label], ["#alias", alias], ...]
		# objects: [id_obj, ...]
		# data: {id_obj: {cls_id: value, #alias: value, ...}, ...}
		
		obj_id, rel_label, cls_label, cls_id, reversed = self._relation
		
		ret = ([], [], {})
		slice = self._store._db.relations[self._store._db.relations[:,0 if reversed else 2] == obj_id]
		if not slice.size:
			return ret
		slice = slice[slice[:,3] == rel_label]
		if not slice.size:
			return ret
		objects = slice[:,2 if reversed else 0]
		if cls_id is None:
			cls_members = self._store._db.objects[~np.in1d(self._store._db.objects, self._store._db.members[:,1])]
		else:
			cls_members = self._store._db.members[self._store._db.members[:,0] == cls_id, 2]
			cls_members = cls_members[cls_members.astype("<U3") == self._store.get_dep_class_prefix("Object")]
		if not cls_members.size:
			return ret
		objects = objects[np.in1d(objects, cls_members)]
		if not objects.size:
			return ret
		objects = sorted(objects, key = lambda obj_id2: id_to_int(obj_id2))
		return self._find_descriptors(objects)
	
	def _process_class(self):
		# return [columns, objects, data]
		# columns: [[cls_id, label], ["#alias", alias], ...]
		# objects: [id_obj, ...]
		# data: {id_obj: {cls_id: value, #alias: value, ...}, ...}
		
		ret = ([], [], {})
		if not self._store._db.members.size:
			return ret
		objects = self._store._db.members[self._store._db.members[:,0] == self._cls_id, 2]
		objects = objects[objects.astype("<U3") == self._store.get_dep_class_prefix("Object")]
		if not objects.size:
			return ret
		
		return self._find_descriptors(objects)
		
		
		