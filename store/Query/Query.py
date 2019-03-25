from deposit.store.DLabel.DString import (DString)
from deposit.store.DElements.DClasses import (DClass)
from deposit.store.DElements.DDescriptors import (DDescriptor)
from deposit.store.Query.Parse import (Parse)

from collections import defaultdict
from itertools import product

class Query(object):
	
	def __init__(self, store, querystr):
		
		self.store = store
		self.querystr = querystr
		
		self._rows = []
		self._columns = []
		self._classes = []
		
		self.parse = None
		
		self.hash = [] # hash of the query rows (to quickly check whether query has changed)
		
		self.process()
	
	def add(self, row):
	
		self._rows.append(row)
		for name in row:
			if not name in self._columns:
				self._columns.append(name)
	
	def get_objects_by_classes(self, classes):
		
		def get_object_ids_by_class(cls):
			
			if cls == "!*":
				ids = set()
				for id in self.store.objects:
					if len(self.store.objects[id].classes) == 0:
						ids.add(id)
				return ids
			return self.store.classes[cls].objects.keys()
		
		ids = set()
		for cls in classes:
			ids.update(get_object_ids_by_class(cls))
		return [self.store.objects[id] for id in ids]
	
	def check_conditions(self, objects):
		
		for condition in self.parse.conditions:
			if not condition.eval(objects):
				return False
		return True
	
	def process(self):
		
		self.parse = Parse(self.store, self.querystr)
		
		if self.parse.query_type == "ADD RELATION":
			rel, wherestr_from, wherestr_to = self.parse.add_relation
			query_from = Query(self.store, "SELECT * WHERE " + wherestr_from)
			query_to = Query(self.store, "SELECT * WHERE " + wherestr_to)
			for row_from in query_from:
				for row_to in query_to:
					row_from.object.relations.add(rel, row_to.object)
			return
		
		if self.parse.query_type != "SELECT":
			return
		
		if not self.parse.selects:
			return
		
		objects = defaultdict(dict)  # {classstr: {index: [DObject, ...], ...}, ...}
		
		# collect classstr, index and objects to initialize chains
		classstr_index0s = []
		# for first Select
		classstr0, index0 = self.parse.selects[0].classstr, self.parse.selects[0].index
		classstr_index0s.append((classstr0, index0))
		objects[classstr_index0s[0][0]][classstr_index0s[0][1]] = self.get_objects_by_classes(self.parse.selects[0].classes)
		# for first Related of each relation chain
		for chain in self.parse.relations:
			related = chain[0]
			classstr_index1 = (related.classstr1, related.index1)
			classstr_index2 = (related.classstr2, related.index2)
			if (classstr_index1 not in classstr_index0s) and (classstr_index2 not in classstr_index0s):
				classstr_index0s.append(classstr_index1)
				objects[related.classstr1][related.index1] = self.get_objects_by_classes(related.classes1)
		
		collect = []
		for classstr, index in classstr_index0s:
			if ("*" not in classstr) and (("*", index) in classstr_index0s):
				continue
			collect.append((classstr, index))
		classstr_index0s = collect
		
		self._classes = list(self.parse.selects[0].classes)
		
		# collect selects and objects which are not present in relations
		def in_relations(select):
			
			for rel_chain in self.parse.relations:
				for related in rel_chain:
					if ((select.classstr == related.classstr1) and (select.index == related.index1)) or ((select.classstr == related.classstr2) and (select.index == related.index2)):
						return True
			return False
		
		classstr_index_selects_only = set()  # set((classstr, index), ...); present only in selects (not in relations)
		for select in self.parse.selects:
			if not in_relations(select):
				if (select.classstr, select.index) == (classstr0, index0):
					continue
				objects[select.classstr][select.index] = self.get_objects_by_classes(select.classes)
				classstr_index_selects_only.add((select.classstr, select.index))
		
		# collect object chains
		def in_chains(chain, done):
			
			ids = []
			for classstr in chain:
				for index in chain[classstr]:
					ids.append(chain[classstr][index].id)
			ids = set(ids)
			for ids2 in done:
				if ids.issubset(ids2):
					return True
			done.add(tuple(ids))
			return False
		
		def get_chains(chain, rel_chain, chains, done):
			# recursively fill chain and append it to chains
			
			while rel_chain:
				
				related = rel_chain.pop(0)
				
				reversed = False
				if (related.classstr1 in chain) and (related.index1 in chain[related.classstr1]):
					obj1 = chain[related.classstr1][related.index1]
				elif (related.classstr2 in chain) and (related.index2 in chain[related.classstr2]):
					obj1 = chain[related.classstr2][related.index2]
					reversed = True
				else:
					break
				
				if reversed:
					objects2 = related.get_objects1(obj1)
				else:
					objects2 = related.get_objects2(obj1)
				
				for obj2 in objects2:
					if reversed:
						get_chains(dict(chain, **{related.classstr1: {related.index1: obj2}}), rel_chain, chains, done)
					else:
						get_chains(dict(chain, **{related.classstr2: {related.index2: obj2}}), rel_chain, chains, done)
			
			if not in_chains(chain, done):
				chains.append(chain)
		
		chains = []  # [{classstr: {index: DObject, ...}, ...}, ...]
		for objects0 in product(*[objects[classstr][index] for classstr, index in classstr_index0s]):
			chain = {}
			for i, classstr_index in enumerate(classstr_index0s):
				if classstr_index[0] not in chain:
					chain[classstr_index[0]] = {}
				chain[classstr_index[0]][classstr_index[1]] = objects0[i]
			chains_obj0 = []
			
			# collect chains given by relations
			for rel_chain in self.parse.relations:
				chains_obj0.append([])
				done = set()
				get_chains(chain, rel_chain.copy(), chains_obj0[-1], done)
			
			if not chains_obj0:
				chains_obj0 = [[chain]]
			
			# collect chains given by selects only
			for classstr, index in classstr_index_selects_only:
				chains_obj0.append([])
				for obj in objects[classstr][index]:
					chains_obj0[-1].append({classstr: {index: obj}})
			
			# combine chains and check conditions
			for chains_rel in product(*[chains_obj for chains_obj in chains_obj0]):
				chain = {}
				for chain_rel in chains_rel:
					chain.update(chain_rel)
				if self.check_conditions(chain):
					chains.append(chain)
		
		# apply conditions, aliases & sums
		done = set() # to avoid duplicates
		for chain in chains:
			# create row
			row = QueryRow(self, chain[classstr0][index0])
			# add descriptor values based on selects
			for select in self.parse.selects:
				obj = select.get_object(chain)
				if obj is None:
					continue
				classes = []
				if select.classes == {"!*"}:
					classes = [DClass(self.store.classes, "[no class]")]
				for cls in select.classes:
					if cls != "!*":
						classes.append(self.store.classes[cls])
				if len(select.descriptors) == 0:
					for cls in classes:
						row.add(obj, cls)
				for descr in select.descriptors:
					for cls in classes:
						if not descr in obj.descriptors:
							row.add(obj, cls)
						else:
							row.add(obj, cls, obj.descriptors[descr])
			
			if len(row) and (row.hash not in done):
				self.add(row)
				done.add(row.hash)
		
		# add counts as aliases
		for count_ in self.parse.counts:
			for row in self._rows:
				cnt = 0
				for chain in chains:
					if (chain[classstr0][index0].id == row.object.id) and count_.eval(chain):
						cnt += 1
				row.add_alias(count_.alias, cnt)
		
		# add sums as aliases
		for sum_ in self.parse.sums:
			for row in self._rows:
				summed = 0
				for chain in chains:
					if (chain[classstr0][index0].id == row.object.id):
						summed += sum_.value(chain)
				row.add_alias(sum_.alias, summed)
		
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
	
	@property
	def query_type(self):
		# returns SELECT, INSERT, ADD RELATION, ADD CLASS, ...
		
		return self.parse.query_type
	
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
		return "id %d, %s" % (self.object.id, ", ".join([("%s: id %d" % (name, self[name].object.id) if (self[name].descriptor is None) else "%s: %s" % (name, str(self[name].descriptor.label))) for name in self]))

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

