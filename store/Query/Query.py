'''
	Query string:

	SELECT [select1], [select2] WHERE [chain1] and/or/+/-/... [chain2] QUANTIFY [chain1] and/or/+/-/... [chain2] SUM [class].[descriptor] AS [alias]

	alternatives:

	SELECT [select]
	SELECT [select] WHERE [chain]
	SELECT [select] QUANTIFY [chain] AS [alias]
	SELECT [select] QUANTIFY [chain] SUM [class].[descriptor] AS [alias]
	SELECT [select] WHERE [chain] QUANTIFY [chain] AS [alias]
	SELECT [select] WHERE [chain] QUANTIFY [chain] SUM [class].[descriptor] AS [alias]
	SELECT [select] QUANTIFY [chain] AS [alias] QUANTIFY [chain] AS [alias] ...

	[select]:
		1. class
		2. class.descriptor
		
		* instead of class / descriptor means any class / descriptor

	[chain]:
		1. class.descriptor	(or obj(id).descriptor)
		2. class.relation.[1. or 2.]	(or obj(id).relation.[1. or 2.])
		
		* instead of class / descriptor / relation means any class / descriptor / relation
		!* instead of class / decriptor means no class / descriptor
		!class / !descriptor / !relation means all except class / descriptor / relation

	[alias]:
		column name under which to display the quantity
		if an alias has the same name as a regular column or another alias, an underscore will be added to it

	Parts of the query string can be quoted to allow class names with a dot (e.g. 'Cls.1', "Class.One") or to denote string constants (e.g. cls1.descr1 == "one")

	-------------------------------------------------------
	
	Examples of [chain]:
	
	cls1
		all objects which are members of cls1
		
	cls1.rel1
		all members of cls1, related by rel1 to any other object

	cls1.rel1.cls2.descr1
		all members of cls1, related by rel1 to members of cls2, to which descr1 is related by any label

	cls1.rel1.cls2.descr1 > 3
		all members of cls1, related by rel1 to members of cls2, to which descr1 is related by a label >3

	obj(id)
		object with id

	cls1.rel1.obj(id)
		all members of cls1, related by rel1 to object(id)

	obj(id).rel1.cls1
		all members of cls1, to which object(id) is related to by rel1
	
	-------------------------------------------------------
	
	Examples of [select]
	
	SELECT cls1
		-> all members of cls1
	SELECT cls1.*
		-> all members of cls1 with all their descriptors
	SELECT cls1, cls2
		-> cartesian product of members of cls1 and cls2
	SELECT cls1.descr1, cls2.descr1
		-> cartesian product of members of cls1 with descriptor descr1 and cls2 with descriptor descr2
	SELECT cls1.descr1, cls2.descr1 WHERE cls1.descr1 == 3
		-> cartesian product of members of cls1 with descriptor descr1 and cls2 with descriptor descr2 == 3
	SELECT cls1.descr1, cls2.descr1 WHERE cls1.rel1.cls2.rel2.cls3
		-> all combinantions of members of cls1 and cls2 where a member of cls1 is related by rel1 to a member of cls2 which is related by rel2 to a member of cls3

'''

from deposit.store.DLabel.DNone import (DNone)
from deposit.store.DLabel.DString import (DString)
from deposit.store.DElements.DClasses import (DClass)
from deposit.store.DElements.DDescriptors import (DDescriptor)
from deposit.store.Query.Parse import (Parse)
from deposit.store.Query.EvalLabel import (EvalLabel)
from deposit.store.Conversions import (to_unique)

from itertools import product

class Query(object):

	def __init__(self, store, querystr, quantify_row = None):

		self.store = store
		self.querystr = querystr
		self.quantify_row = quantify_row

		self._rows = []
		self._columns = []
		self._classes = []

		self.parse = None

		self.hash = [] # hash of the query rows (to quickly check whether query has changed)

		self._process()

	def add(self, row):

		self._rows.append(row)
		for name in row:
			if not name in self._columns:
				self._columns.append(name)

	def _process(self):

		self.parse = Parse(self.store, self.querystr)

		# print() # DEBUG
		# print("QRY:", self.querystr)
		# print("EVAL:", self.parse.eval_str)
		# print("SEL:", self.parse.selects)
		# print("CHAINS:", self.parse.chains)
		# print("QUANTIFIERS:", self.parse.quantifiers)
		# print() # DEBUG

		if not self.parse.selects:
			return

		selects = [(select if (len(select) == 2) else (select[0], None)) for select in self.parse.selects]  # [[cls, descr], ...]

		def process_chains(selects):
			# return rows, where_classes
			# rows = [[id, ...], ...]
			# where_classes = [name, ...]
			
			def get_chain_classes(chain):
				
				collect = []
				for i in range(0, len(chain), 2):
					cls = chain[i]
					if cls == "*":
						return list(self.store.classes.keys())
					elif cls.startswith("obj("):
						id = int(cls[4:-1])
						if id in self.store.objects:
							for cls2 in self.store.objects[id].classes:
								if cls2 not in collect:
									collect.append(cls2)
					elif cls in self.store.classes:
						if cls not in collect:
							collect.append(cls)
				return collect
			
			def get_class_objects(cls):
				# cls = "*" / "!*" / "[class name]" / "![class name]" / "obj([id])"

				if cls == "*":
					return list(self.store.objects.keys())
				
				if cls == "!*":
					return [id for id in self.store.objects if not len(self.store.objects[id].classes)]
				
				if cls.startswith("!"):
					cls = cls[1:]
					return [id for id in self.store.objects if cls not in self.store.objects[id].classes]
				
				if cls.startswith("obj("):
					id = int(cls[4:-1])
					if id in self.store.objects:
						return [id]
					return []
				
				if cls in self.store.classes:
					return [id for id in self.store.classes[cls].objects]
				
				return []

			def get_obj_descr(id, descr):
				# descr = "*" / "!*" / "[descr name]" / "![descr name]"
				# returns [value, ...] / [] / value
				
				if descr == "*":
					return [self.store.objects[id].descriptors[name].label.value for name in self.store.objects[id].descriptors]
				
				if descr == "!*":
					return (len(self.store.objects[id].descriptors) == 0)
				
				if descr.startswith("!"):
					descr = descr[1:]
					return [self.store.objects[id].descriptors[name].label.value for name in self.store.objects[id].descriptors if name != descr]
				
				if descr:
					if descr in self.store.objects[id].descriptors:
						return self.store.objects[id].descriptors[descr].label.value
					return False
				
				return False

			def get_obj_related(id, rel, cls):
				# rel = "*" / "!*" / "[relation name]" / "![relation name]"
				# returns [id, ...] / [] / True / False
				
				def check_class(obj_id, cls):
					
					if cls == "*":
						return True
					
					if cls == "!*":
						return (len(self.store.objects[obj_id].classes) == 0)
					
					if cls.startswith("!"):
						return (obj_id not in self.store.objects[obj_id].classes)
					
					if cls.startswith("obj("):
						return (obj_id == int(cls[4:-1]))
					
					if cls in self.store.objects[obj_id].classes:
						return True
					
					return False
				
				if rel == "*":
					collect = []
					for rel in self.store.objects[id].relations:
						for id2 in list(self.store.objects[id].relations[rel].keys()):
							if check_class(id2, cls):
								collect.append(id2)
					return collect
				
				if rel == "!*":
					return (len(self.store.objects[id].relations) == 0)
				
				if rel.startswith("!"):
					rel = rel[1:]
					collect = []
					for rel2 in self.store.objects[id].relations:
						if rel2 != rel:
							for id2 in list(self.store.objects[id].relations[rel2].keys()):
								if check_class(id2, cls):
									collect.append(id2)
					return collect
				
				if rel:
					collect = []
					for id2 in list(self.store.objects[id].relations[rel].keys()):
						if check_class(id2, cls):
							collect.append(id2)
					return collect
				
				return []

			def get_chain_rows(chain, cls0, id0):
				# returns [id, ..., value]
				
				chain = chain.copy()
				
				if len(chain) == 1: # c
					cls = chain[0]
					if cls == cls0:
						ids = [id0]
					else:
						ids = get_class_objects(cls)
					return [[id, True] for id in ids]

				if len(chain) == 2: # c.d
					cls, descr = chain
					if cls == cls0:
						ids = [id0]
					else:
						ids = get_class_objects(cls)
					collect = []
					for id in ids:
						values = get_obj_descr(id, descr) # [value, ...] / [] / value
						if values:
							if isinstance(values, list):
								for value in values:
									collect.append([id, value])
							else:
								collect.append([id, values])
					return collect
				
				if chain: # c.r.c / c.r...c.d
					descr = None
					if len(chain) % 2 == 0: # c.r...c.d
						descr = chain.pop()
					cls = chain.pop(0)
					if cls == cls0:
						id_rows = [[id0]]
					else:
						id_rows = [[id] for id in get_class_objects(cls)]
					while chain and id_rows:
						rel = chain.pop(0)
						cls = chain.pop(0)
						collect = []
						for id_row in id_rows:
							ids = get_obj_related(id_row[-1], rel, cls) # [id, ...] / [] / True / False
							if isinstance(ids, list):
								for id in ids:
									collect.append(id_row + [id])
							elif ids == True:
								collect.append(id_row)
						id_rows = collect
						if rel == "!*":
							break
					if descr is None:
						id_rows = [id_row + [True] for id_row in id_rows]
					else:
						collect = []
						for id_row in id_rows:
							values = get_obj_descr(id_row[-1], descr)
							if values:
								if isinstance(values, list):
									for value in values:
										collect.append(id_row + [value])
								else:
									collect.append(id_row + [values])
						id_rows = collect
					return id_rows
				
				return []

			def eval_row(chains_rows, idxs):

				vars = []
				values = {}
				n = 0
				for i in range(len(self.parse.chains)):
					n += 1
					while ("_v" + str(n)) in self.parse.eval_str:
						n += 1
					vars.append("_v" + str(n))
					values[vars[-1]] = EvalLabel(chains_rows[i][idxs[i]][-1])
				return eval(self.parse.eval_str % (tuple(vars)), values)

			where_classes = []
			for chain in self.parse.chains:
				for cls in get_chain_classes(chain):
					if cls not in where_classes:
						where_classes.append(cls)

			rows = []
			cls_id_row = None
			if where_classes:

				chain_classes_lookup = {}  # {chain_idx: {cls: idx, ...}, ...}
				for chain_idx, chain in enumerate(self.parse.chains):
					chain_classes_lookup[chain_idx] = {}
					for idx, cls in enumerate([chain[j] for j in range(0, len(chain), 2)]):
						chain_classes_lookup[chain_idx][cls] = idx

				cls0s = self.parse.chains[0][0]
				if cls0s == "*":
					cls0s = list(self.store.classes.keys())
				else:
					cls0s = [cls0s]
				if not cls0s:
					cls0s = ["!*"]
				if selects[0][0] in self.store.classes:
					cls_id_row = selects[0][0]
				for cls0 in cls0s:
					id0s = get_class_objects(cls0)
					for id0 in id0s:
						id_row = id0
						chains_rows = [get_chain_rows(chain, cls0, id0) for chain in self.parse.chains] # [[id, ..., value], ...]; in order of chains
						for idxs in product(*[range(len(chains_rows[j])) for j in range(len(chains_rows))]):
							if eval_row(chains_rows, idxs):
								row = []
								for k in range(len(self.parse.chains)):
									ids = chains_rows[k][idxs[k]][:-1]
									if ids:
										row += ids
										if (cls_id_row is not None) and (cls_id_row in chain_classes_lookup[k]):
											id_row = ids[chain_classes_lookup[k][cls_id_row]]
									else:
										row = []
										break
								if row:
									rows.append([id_row] + sorted(to_unique(row)))

			return rows, where_classes
		
		rows, where_classes = process_chains(selects)
		
		self._classes = list(set([cls for cls, _ in selects] + where_classes))

		def update_rows(rows, selects, where_classes):
			# check if any of the select classes are missing in where_classes
			# if yes add their ids to rows as cartesian product
			#
			# rows = [[id, ...], ...]
			# selects = [[cls, descr], ...]
			# where_classes = [name, ...]

			done = []
			for cls, descr in selects:
				if cls in done:
					continue
				ids = None
				if (cls == "*" and not where_classes):
					ids = list(self.store.objects.keys())
				elif (cls != "*") and (not cls in where_classes):
					if cls == "!*":
						ids = [id for id in self.store.objects if not self.store.objects[id].classes]
					else:
						ids = [id for id in self.store.classes[cls].objects]
				done.append(cls)
				if ids:
					collect = []
					if rows:
						for row in rows:
							for id in ids:
								collect.append(row + [id])
					else:
						collect = [[id, id] for id in ids]
					rows = collect

			return rows

		rows = update_rows(rows, selects, where_classes) # check if any of the select classes are missing in where_classes, if yes add their ids to rows as cartesian product

		def add_query_rows(rows, selects):
			# generate query rows from rows according to selects
			# rows = [[id, ...], ...]
			# selects = [[cls, descr], ...]

			cls_descrs = []  # [[cls, descr], ...]
			for cls, descr in selects:
				if (cls == "*") and (descr == "*"):
					for row in rows:
						obj = self.store.objects[row[0]]
						classes = list(obj.classes.keys())
						descriptors = list(obj.descriptors.keys())
						for cls2 in classes:
							for descr2 in descriptors:
								if [cls2, descr2] not in cls_descrs:
									cls_descrs.append([cls2, descr2])
				elif (cls == "!*") and (descr == "*"):
					for row in rows:
						obj = self.store.objects[row[0]]
						if not len(obj.classes.keys()):
							for descr2 in obj.descriptors:
								if ["!*", descr2] not in cls_descrs:
									cls_descrs.append(["!*", descr2])
				elif cls == "*":  # *.[descriptor]
					for row in rows:
						obj = self.store.objects[row[0]]
						classes = list(obj.classes.keys())
						if classes:
							for cls2 in classes:
								if [cls2, descr] not in cls_descrs:
									cls_descrs.append([cls2, descr])
						elif ["!*", descr] not in cls_descrs:
							cls_descrs.append(["!*", descr])
				elif (not "*" in cls) and (descr == "*"):  # [class].*
					for descr in self.store.classes[cls].descriptors:
						if [cls, descr] not in cls_descrs:
							cls_descrs.append([cls, descr])
				else:  # !*.[descriptor] or [class].[descriptor]
					if [cls, descr] not in cls_descrs:
						cls_descrs.append([cls, descr])

			done = []
			for row in rows:
				qry_row = QueryRow(self, self.store.objects[row[0]])
				for cls, descr in cls_descrs:
					descriptor = None
					obj = None
					for id in row[1:]:
						obj = self.store.objects[id]
						if (cls in obj.classes) or ((cls == "!*") and (len(self.store.objects[id].classes) == 0)):
							if descr is None:
								break
							if descr in obj.descriptors:
								descriptor = obj.descriptors[descr]
								break
					if descriptor is None:
						if obj is None:
							obj = self.store.objects[row[0]]
						if descr is not None:
							descriptor = DDescriptor(obj, self.store.classes[descr], DNone())
					if cls == "!*":
						cls = DClass(obj.classes, "[no class]")
					else:
						cls = self.store.classes[cls]
					qry_row.add(obj, cls, descriptor)

				if self.parse.chains and len(qry_row):
					if qry_row.hash in done:
						continue
					else:
						done.append(qry_row.hash)

				for alias in self.parse.quantifiers:
					query = Query(self.store, "SELECT %s WHERE %s" % tuple(self.parse.quantifiers[alias]), row)
					select = self.parse.quantifiers[alias][0]
					if select == "*":
						quantity = len(query)
					else:
						quantity = 0
						for row in query:
							val = row[select].descriptor
							if val is None:
								continue
							try:
								quantity += float(val.label.value)
							except:
								continue

					if quantity - int(quantity) == 0:
						quantity = int(quantity)

					qry_row.add_alias(alias, quantity)

				self.add(qry_row)

		add_query_rows(rows, selects) # generate query rows from rows according to selects

		self.hash = self.columns + [row.hash for row in self._rows]

	@property
	def columns(self):

		if len(self._rows):
			return self._columns.copy()
		collect = []
		for cls in self._classes:
			if "*" not in cls:
				for descr in self.store.classes[cls].descriptors:
					collect.append("%s.%s" % (cls, descr))
		return collect

	@property
	def classes(self):

		return self._classes.copy()

	def __len__(self):

		return len(self._rows)

	def __bool__(self):

		return len(self._rows) > 0

	def __getitem__(self, idx):

		if idx < len(self._rows):
			return self._rows[idx]
		raise IndexError()

	def __setitem__(self, idx, row):

		raise Exception("Impossible to alter a Query")

	def __iter__(self):

		for row in self._rows:
			yield row

	def __delitem__(self, idx):

		raise Exception("Impossible to alter a Query")

class QueryRow(object):

	def __init__(self, parent, object):

		self.parent = parent # a Store or DElement object
		self.object = object # the object by which the chains are evaluated
		self._members = {} # {key: object instance, ...}
		self._keys = [] # [key, ...]
		self._data = [] # [[object, class, descriptor], ...]
		self._pos = 0

		self._hash = None
		self._populated = False

	def add(self, obj, dclass, descriptor = None):

		self._data.append([obj, dclass, descriptor])

	def add_alias(self, alias, value):

		while alias in self:
			alias = alias + "_"
		self[alias] = QueryItem(self, self.object, DClass(self.object, alias), DDescriptor(self.object, DClass(self.object, "[no class]"), DString(value)))

	def set_object(self, object):

		self.object = object

	def keys(self):

		return self._keys.copy()

	def _populate(self):

		if not self._populated:
			self._populated = True
			self.hash  # generate hash first
			for obj, dclass, descriptor in self._data:
				item = QueryItem(self, obj, dclass, descriptor)
				if descriptor is None:
					name = dclass.name
				else:
					name = ".".join([dclass.name, descriptor.dclass.name])
				name2 = name
				n = 2
				while name2 in self:
					name2 = "%s#%d" % (name, n)
					n += 1
				if name2 != name:
					if self[name].descriptor == descriptor:
						continue
				self[name2] = item
				if (name2 != name) and (n == 3):
					self._rename_key(name, "%s#1" % name)
			self._data = None

	def __len__(self):

		if self._populated:
			return len(self._keys)
		return len(self._data)

	def __contains__(self, key):

		self._populate()
		return key in self._keys

	def __getitem__(self, key):

		self._populate()
		if key in self._members:
			return self._members[key]
		return QueryItem(None, None, None)

	def __setitem__(self, key, member):

		self._populate()
		self._members[key] = member
		if not key in self._keys:
			self._keys.append(key)

	def _rename_key(self, old_key, new_key):

		self._members[new_key] = self._members.pop(old_key)
		self._keys[self._keys.index(old_key)] = new_key

	def __iter__(self):

		self._populate()
		for key in self._keys:
			yield key

	def __next__(self):

		self._populate()
		if self._pos < len(self._keys):
			self._pos += 1
			return self._keys[self._pos - 1]
		else:
			self._pos = 0
			raise StopIteration()

	def __delitem__(self, key):

		self._populate()
		if key in self._members:
			del self._members[key]
			self._keys.remove(key)

	def __str__(self):

		self._populate()
		return "obj(%d) %s" % (self.object.id, ", ".join([("%s: obj(%d)" % (name, self[name].object.id) if (self[name].descriptor is None) else "%s: %s" % (name, str(self[name].descriptor.label))) for name in self]))

	def __repr__(self):

		self._populate()
		value = self.__str__()
		if not value is None:
			value = value.encode("utf-8")
		return value

	@property
	def hash(self):

		if self._hash is None:
			self._hash = "".join([str(obj.id if (descriptor is None) else descriptor.label.value) for obj, _, descriptor in self._data])
		return self._hash

class QueryItem(object):

	def __init__(self, parent, object, dclass, descriptor = None):

		self.parent = parent
		self.object = object
		self.dclass = dclass
		self.descriptor = descriptor
