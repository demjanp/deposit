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

from collections import defaultdict

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
			if not condition.check(objects):
				return False
		return True
	
	def process(self):
		
		self.parse = Parse(self.store, self.querystr)
		if not self.parse.selects:
			return
		
		# collect objects for all combinations of classstr and index based on selects and relations
		objects = defaultdict(dict)  # {classstr: {index: [DObject, ...], ...}, ...}
		for select in self.parse.selects:
			if select.index in objects[select.classstr]:
				continue
			objects[select.classstr][select.index] = self.get_objects_by_classes(select.classes)
		for related in self.parse.relations:
			if related.index1 not in objects[related.classstr1]:
				objects[related.classstr1][related.index1] = self.get_objects_by_classes(related.classes1)
			if related.index2 not in objects[related.classstr2]:
				objects[related.classstr2][related.index2] = self.get_objects_by_classes(related.classes2)
		
		# collect all possible rows according to selects and relations
		classstr_index_related = set()  # set((classstr, index), ...); present in relations
		classstr_index_selects = set()  # set((classstr, index), ...); present in selects
		for related in self.parse.relations:
			if (related.classstr1, related.index1) not in classstr_index_related:
				classstr_index_related.add((related.classstr1, related.index1))
			if (related.classstr2, related.index2) not in classstr_index_related:
				classstr_index_related.add((related.classstr2, related.index2))
		for select in self.parse.selects:
			if (select.classstr, select.index) not in classstr_index_selects:
				classstr_index_selects.add((select.classstr, select.index))
		classstr_index_all = classstr_index_related.union(classstr_index_selects)
		classstr_index_selects_only = classstr_index_selects.difference(classstr_index_related)  # set((classstr, index), ...); present only in selects (not in relations)
		
		def related_is_relevant(classstr1, index1, classstr2, index2, chain):
			
			return (classstr1 in chain) and (index1 in chain[classstr1]) and ((classstr2 not in chain) or (index2 not in chain[classstr2]))
		
		def get_chains(chain, chains):
			# recursively fill chain and if full, append it to chains
			# chain = {classstr: {index: DObject, ...}, ...}
			
			for related in self.parse.relations:
				if related_is_relevant(related.classstr1, related.index1, related.classstr2, related.index2, chain):
					obj1 = chain[related.classstr1][related.index1]
					for obj2 in objects[related.classstr2][related.index2]:
						if related.check(obj1, obj2):
							get_chains(dict(chain, **{related.classstr2: {related.index2: obj2}}), chains)
				if related_is_relevant(related.classstr2, related.index2, related.classstr1, related.index1, chain):
					obj1 = chain[related.classstr2][related.index2]
					for obj2 in objects[related.classstr1][related.index1]:
						if related.check(obj1, obj2):
							get_chains(dict(chain, **{related.classstr1: {related.index1: obj2}}), chains)
			for classstr, index in classstr_index_selects_only:
				if (classstr not in chain) or (index not in chain[classstr]):
					for obj2 in objects[classstr, index]:
						get_chains(dict(chain, **{classstr: {index: obj2}}), chains)
			chains.append(chain)
		
		# collect object chains
		chains = []  # [{classstr: {index: DObject, ...}, ...}, ...]
		classstr0 = self.parse.selects[0].classstr
		index0 = self.parse.selects[0].index		
		for obj0 in objects[classstr0][index0]:
			get_chains({classstr0: {index0: obj0}}, chains)
		
		# apply conditions, aliases & sums
		done = set() # to avoid duplicates
		for chain in chains:
			if not self.check_conditions(chain):
				continue
			# create row
			row = QueryRow(self, chain[classstr0][index0])
			# add descriptor values based on selects
			for select in self.parse.selects:
				obj = select.get_object(chain)
				classes = []
				if "!*" in select.classes:
					classes = [DClass(self.store.classes, "[no class]")]
				for cls in select.classes:
					if cls != "!*":
						classes.append(self.store.classes[cls])
				if len(select.descriptors) == 0:
					for cls in classes:
						row.add(obj, cls)
				for descr in select.descriptors:
					for cls in classes:
						if obj is None:
							row.add(obj, cls, DDescriptor(None, self.store.classes[descr], DNone()))
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
					if (chain[classstr0][index0].id == row.object.id) and count_.check(chain):
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

