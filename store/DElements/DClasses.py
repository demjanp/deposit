
from deposit import Broadcasts
from deposit.store.DElements.DElements import (DElement, DElements, event, blocked)
from deposit import (INVALID_CHARACTERS_NAME)

from collections import defaultdict

class DClass(DElement):
	
	def __init__(self, parent, name, order = -1, linked = None):
		# linked = linked database identifier
		
		super(DClass, self).__init__(parent)
		
		self.name = name
		self.order = order
		self.linked = linked

		self._objects = None
		self._subclasses = None
		self.descriptors = []  # [name, ...]
		self.relations = defaultdict(list)  # {name: [class_name, ...], ...}
	
	@property
	def key(self):
		
		return self.name
	
	@property
	def objects(self):

		if not isinstance(self._objects, self.store.DOBJECTS):
			if self._objects is None:
				self._objects = self.store.DOBJECTS(self)
			elif isinstance(self._objects, list):
				collect = self.store.DOBJECTS(self)
				for id in self._objects:
					collect[id] = self.store.objects[id]
				self._objects = collect
			else:
				raise Exception("DClass._objects is wrong type:", type(self._objects))
			self._objects.set_on_added(self.on_object_added)
			self._objects.set_on_deleted(self.on_object_deleted)
		return self._objects

	def on_object_added(self, obj):

		obj.classes[self.name] = self
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)

	def on_object_deleted(self, obj):

		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)

	@property
	def subclasses(self):
		
		if not isinstance(self._subclasses, DClasses):
			if self._subclasses is None:
				self._subclasses = DClasses(self)
			elif isinstance(self._subclasses, list):
				collect = DClasses(self)
				for name in self._subclasses:
					collect[name] = self.store.classes[name]
				self._subclasses = collect
			else:
				raise Exception("DClass._subclasses is wrong type:", type(self._subclasses))
			self._subclasses.set_on_added(self.on_subclass_added)
			self._subclasses.set_on_deleted(self.on_subclass_deleted)
		return self._subclasses

	def on_subclass_added(self, dclass):

		self.broadcast(Broadcasts.ELEMENT_CHANGED, dclass)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)

	def on_subclass_deleted(self, dclass):

		self.broadcast(Broadcasts.ELEMENT_CHANGED, dclass)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
	
	@blocked
	@event
	def add_descriptor(self, name):

		if not name in self.descriptors:
			if name not in self.store.classes:
				self.store.classes.add(name)
			self.descriptors.append(name)
			self.descriptors = sorted(self.descriptors, key=lambda name: self.store.classes[name].order)
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
	
	@blocked
	@event
	def rename_descriptor(self, old_name, new_name):
		
		self.descriptors.remove(old_name)
		self.add_descriptor(new_name)
		for id in self.objects:
			self.objects[id].descriptors.rename(old_name, new_name)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
	
	@blocked
	@event	
	def del_descriptor(self, name):

		if not name in self.descriptors:
			return
		
		# also delete descriptor from classes objects
		for id in self.objects:
			del self.objects[id].descriptors[name]

		self.descriptors.remove(name)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
	
	@blocked
	@event
	def add_relation(self, rel, class_name):

		if class_name not in self.relations[rel]:
			self.relations[rel].append(class_name)
			self.relations[rel] = sorted(self.relations[rel], key=lambda class_name: self.store.classes[class_name].order if (class_name != "!*") else -1)
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
	
	@blocked
	@event
	def del_relation(self, rel, class_name):

		if (rel in self.relations) and (class_name in self.relations[rel]):
			self.relations[rel].remove(class_name)
			if not len(self.relations[rel]):
				del self.relations[rel]
				self.broadcast(Broadcasts.ELEMENT_CHANGED, self)
			# also delete relation from classes objects
			for id1 in self.objects:
				if rel not in self.objects[id1].relations:
					continue
				to_del = []
				for id2 in self.objects[id1].relations[rel]:
					if class_name in self.store.objects[id2].classes:
						to_del.append(id2)
				for id2 in to_del:
					del self.store.objects[id1].relations[rel][id2]
	
	@blocked
	def add_object(self):
		
		return self.objects.add()
	
	@blocked
	def del_object(self, id):
		
		del self.objects[id]
	
	@blocked
	def add_subclass(self, cls):
		
		return self.subclasses.add(cls)
	
	@blocked
	def del_subclass(self, name):
		
		del self.subclasses[name]
	
	def to_dict(self):
		
		return dict(
			order = self.order,
			name = self.name,
			linked = self.linked,
			objects = self.objects._keys,
			subclasses = self.subclasses._keys,
			descriptors = self.descriptors,
			relations = dict(self.relations),
			**super(DClass, self).to_dict(),
		)
	
	def from_dict(self, data):
		
		self.order = data["order"]
		self._objects = data["objects"]
		self._subclasses = data["subclasses"]
		if "descriptors" in data:  # TODO will be obsolete for new databases
			self.descriptors = data["descriptors"]
			self.relations = defaultdict(list, data["relations"])
	
	def from_dict_linked(self, data, prefix):
		
		self.from_dict(data)
		self._subclasses = [(prefix + "@" + name) for name in self._subclasses]
		if "descriptors" in data:  # TODO will be obsolete for new databases
			self.descriptors = [(prefix + "@" + name) for name in self.descriptors]
			self.relations = defaultdict(list, [(rel, prefix + "@" + self.relations[rel]) for rel in self.relations])

class DClasses(DElements):
	
	def __init__(self, parent):

		self._on_added = None
		self._on_deleted = None

		super(DClasses, self).__init__(parent)

	def set_on_added(self, func):

		self._on_added = func

	def set_on_deleted(self, func):

		self._on_deleted = func
	
	@blocked
	@event
	def add(self, cls):
		
		if isinstance(cls, DClass):
			name = cls.name
		else:
			name = str(cls)
		if not name in self.store.classes:
			# add to store

			for char in INVALID_CHARACTERS_NAME:
				if char in name:
					raise Exception("Invalid character (%s) in Class name" % (char))

			if len(self.store.classes):
				order = max(self.store.classes[name].order for name in self.store.classes) + 1
			else:
				order = 0
			self.store.classes[name] = DClass(self, name, order)
			self.broadcast(Broadcasts.ELEMENT_ADDED, self.store.classes[name])

		self[name] = self.store.classes[name]
		
		if self.parent.__class__.__name__ == "DClass":
			self.store.events.add(self.parent, self.parent.add_subclass, name)
		elif self.parent.__class__.__name__ == "DObject":
			self.store.events.add(self.parent, self.parent.add_class, name)

		if self._on_added is not None:
			self._on_added(self.store.classes[name])

		return self[name]
	
	@blocked
	@event
	def rename(self, old_cls, new_cls):
		
		if old_cls not in self.store.classes:
			return False
		if new_cls in self.store.classes:
			return False
		old_cls = self.store.classes[old_cls]
		new_cls = self.add(new_cls)

		for id in old_cls.objects:
			old_cls.objects[id].classes.add(new_cls)

		for id in self.store.objects:
			if old_cls.name in self.store.objects[id].descriptors:
				self.store.objects[id]._descriptors.add(new_cls, self.store.objects[id]._descriptors[old_cls.name].label)

		for name2 in self.store.classes:
			if old_cls.name in self.store.classes[name2].subclasses:
				self.store.classes[name2].subclasses.add(new_cls)
			if old_cls.name in self.store.classes[name2].descriptors:
				self.store.classes[name2].add_descriptor(new_cls.name)

		self.switch_order(old_cls.name, new_cls.name)

		del self.store.classes[old_cls.name]

		return True

	def __getitem__(self, key):
		
		if super(DClasses, self).__contains__(key):
			return super(DClasses, self).__getitem__(key)
		return DClass(self, "[no class]")
	
	@blocked
	@event
	def __delitem__(self, name):

		if not name in self:
			return

		if isinstance(self.parent, DElement):
			cls = self.store.classes[name]
			self.del_naive(name)
			
			if self.parent.__class__.__name__ == "DClass":
				self.store.events.add(self.parent, self.parent.del_subclass, name)
			elif self.parent.__class__.__name__ == "DObject":
				self.store.events.add(self.parent, self.parent.del_class, name)
			
		else:
			# delete from store
			cls = self[name]

			# delete from objects
			for id in cls.objects:
				del cls.objects[id].classes[cls.name]

			# delete descriptors with this class
			for id in self.store.objects:
				if cls.name in self.store.objects[id].descriptors:
					del self.store.objects[id]._descriptors[cls.name]

			# delete from subclasses
			for name2 in self.store.classes:
				if cls.name in self.store.classes[name2].subclasses:
					del self.store.classes[name2].subclasses[cls.name]
				if cls.name in self.store.classes[name2].descriptors:
					self.store.classes[name2].del_descriptor(cls.name)

			self.del_naive(name)
			cls = DClass(self, name)
			self.broadcast(Broadcasts.ELEMENT_DELETED, cls)

		if self._on_deleted is not None:
			self._on_deleted(cls)
	
	@blocked
	@event
	def switch_order(self, name1, name2):
		
		if DElements.switch_order(self, name1, name2):
			self[name1].order, self[name2].order = self[name2].order, self[name1].order
			self.update_order_deep()
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self[name1])
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self[name2])
	
	@blocked
	def set_order(self, data):
		# data = {name:, order_nr, ...}
		
		for name in data:
			self[name].order = data[name]
		self.update_order_deep()
	
	@blocked
	def update_order(self):
		
		self._keys = sorted(self._keys, key = lambda key: self[key].order)
	
	def update_order_deep(self):
		
		for name in self:
			self[name].descriptors = sorted(self[name].descriptors, key = lambda descr: self[descr].order)
			for rel in self[name].relations:
				self[name].relations[rel] = sorted(self[name].relations[rel], key = lambda class_name: self[class_name].order)
		for id in self.store.objects:
			self.store.objects[id].classes.update_order()
			self.store.objects[id].descriptors.update_order()
	
	def from_dict(self, data):
		
		names = sorted(data.keys(), key = lambda key: data[key]["order"])
		for name in names:
			self.add_naive(name, DClass(self, name))
		for name in names:
			self[name].from_dict(data[name])
		return self
	
	def from_dict_linked(self, data, identifier):
		
		names = sorted(data.keys(), key = lambda key: data[key]["order"])
		for name in names:
			name_linked = self.store.linked[identifier].prefix + "@" + name
			self._members[name_linked] = DClass(self, name_linked, linked = identifier + name)
			if not name_linked in self._keys:
				self._keys.append(name_linked)
			if not name_linked in self.store.linked[identifier].classes:
				self.store.linked[identifier].classes.append(name_linked)
		for name in names:
			name_linked = self.store.linked[identifier].prefix + "@" + name
			self[name_linked].from_dict_linked(data[name], self.store.linked[identifier].prefix)
		return self

