from deposit import Broadcasts
from deposit.store.DElements.DElements import (DElement, DElements, event, blocked)

class DObjects(DElements):
	
	def __init__(self, parent):

		self._on_added = None
		self._on_deleted = None

		super(DObjects, self).__init__(parent)

	def set_on_added(self, func):

		self._on_added = func

	def set_on_deleted(self, func):

		self._on_deleted = func
	
	@blocked
	def add(self, id = None):
		# returns the added / created object
		
		if (self.parent.__class__.__name__ == "DClass") and (self.parent.name == "[no class]"):
			raise Exception("Attempted to add object to a non-existing class")
		
		add_new = False
		if id is None:
			id = self.get_new_id(self.store.objects)
			add_new = True
		if add_new or (id not in self.store.objects):
			self.store.objects.add_naive(id, DObject(self, id))
		self.broadcast(Broadcasts.ELEMENT_ADDED, self.store.objects[id])

		self[id] = self.store.objects[id]
		
		self.store.events.add(self, self.add, id)
		if self.parent.__class__.__name__ == "DClass":
			self.store.events.add(self.parent, self.parent.add_object, id)

		if self._on_added is not None:
			self._on_added(self.store.objects[id])

		return self[id]
	
	@blocked
	@event
	def __delitem__(self, id):

		if isinstance(self.parent, DElement):
			obj = self.store.objects[id]
			self.del_naive(id)
			
			if self.parent.__class__.__name__ == "DClass":
				self.store.events.add(self.parent, self.parent.del_object, id)

		else:
			# delete from store
			obj = self[id]

			# remove the object from all its classes
			for cls in obj.classes:
				del obj.classes[cls].objects[id]

			# remove all descriptors of the object
			for descr in obj.descriptors.keys():
				del obj.descriptors[descr]

			# remove object from all relations
			for rel in obj.relations.keys():
				rev_name = self.store.reverse_relation(rel)
				for id2 in obj.relations[rel]:
					del obj.relations[rel][id2].relations[rev_name][id]
				if rel in obj.relations:
					del obj.relations[rel][id]

			self.del_naive(id)
			obj = DObject(self, id)
			self.broadcast(Broadcasts.ELEMENT_DELETED, obj)

		if self._on_deleted is not None:
			self._on_deleted(obj)
	
	def from_dict(self, data):
		# note: classes have to be already loaded for this to work
		
		for id in data:
			self.add_naive(id, DObject(self, id))
		for id in self:
			self[id].from_dict(data[id])
	
	def from_dict_linked(self, data, identifier):
		
		ids = {} # {new id: linked id, ...}
		for linked_id in data:
			linked_ident = None
			orig_id = None

			if not "linked" in data[linked_id]:
				data[linked_id]["linked"] = None # DEBUG for compatibility with older format
			
			if data[linked_id]["linked"]:
				linked_ident, orig_id = data[linked_id]["linked"].split("#")
				orig_id = int(orig_id)
			
			if self.store.identifier and (linked_ident == self.store.identifier):
				# object is linked from the local database
				self.store.linked[identifier].object_lookup[linked_id] = orig_id
			
			elif linked_ident:
				# object is linked from a different database
				if orig_id in self.store.linked[linked_ident].object_lookup:
					self.store.linked[identifier].object_lookup[linked_id] = self.store.linked[linked_ident].object_lookup[orig_id]
				else:
					id = self.get_new_id(self)
					self.add_naive(id, DObject(self, id, linked = data[linked_id]["linked"]))
					self.store.linked[linked_ident].object_lookup[orig_id] = id
					self.store.linked[linked_ident].objects[id] = linked_id
					self.store.linked[identifier].object_lookup[linked_id] = id
			
			else:
				# object is from the linked database
				id = self.get_new_id(self)
				self.add_naive(id, DObject(self, id, linked = identifier + str(linked_id)))
				self.store.linked[identifier].objects[id] = linked_id
				self.store.linked[identifier].object_lookup[linked_id] = id
		
		for id in self.store.linked[identifier].objects:
			self[id].from_dict_linked(data[self.store.linked[identifier].objects[id]], identifier)

class DObject(DElement):
	
	def __init__(self, parent, id, linked = None):
		# linked = [linked database identifier]#[linked Object id]
		
		super(DObject, self).__init__(parent)
		
		self.id = id
		self.linked = linked
		self._classes = None
		self._relations = None
		self._descriptors = None
	
	@property
	def key(self):
		
		return self.id
	
	@property
	def classes(self):

		if not isinstance(self._classes, DElements):
			if self._classes is None:
				self._classes = self.store.DCLASSES(self)
			elif isinstance(self._classes, list):
				collect = self.store.DCLASSES(self)
				for name in self._classes:
					collect[name] = self.store.classes[name]
				self._classes = collect
			else:
				raise Exception("DObject._classes is wrong type:", type(self._classes))
			self._classes.set_on_added(self.on_class_added)
			self._classes.set_on_deleted(self.on_class_deleted)
		return self._classes
	
	def first_class(self):
		
		classes = list(self.classes.keys())
		if not classes:
			return "!*"
		return classes[0]
	
	def on_class_added(self, dclass):

		dclass.objects[self.id] = self
		for descr in self.descriptors:
			dclass.add_descriptor(descr)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, dclass)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)

	def on_class_deleted(self, dclass):

		dclass.objects.del_naive(self.id)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, dclass)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self)

	@property
	def relations(self):
		
		if self._relations is None:
			self._relations = self.store.DRELATIONS(self)
		elif isinstance(self._relations, dict):
			self._relations = self.store.DRELATIONS(self).from_dict(self._relations)
		
		return self._relations
	
	@property
	def descriptors(self):
		
		if self._descriptors is None:
			self._descriptors = self.store.DDESCRIPTORS(self)
		elif isinstance(self._descriptors, dict):
			self._descriptors = self.store.DDESCRIPTORS(self).from_dict(self._descriptors)
		
		return self._descriptors
	
	@blocked
	def add_descriptor(self, cls, label, dtype = "DString"):
		
		return self.descriptors.add(cls, label, dtype)
	
	@blocked
	def rename_descriptor(self, old_name, new_name):
		
		return self.descriptors.rename(old_name, new_name)
	
	@blocked
	def del_descriptor(self, name):
		
		del self.descriptors[name]
	
	@blocked
	def add_relation(self, name, target, weight = None):
		
		return self.relations.add(name, target, weight)
	
	@blocked
	def del_relation(self, name, target = None):
		
		if target is None:
			del self.relations[name]
		else:
			del self.relations[name][target]
	
	@blocked
	def set_relation_weight(self, name, target_id, weight):
		
		return self.relations[name].set_weight(target_id, weight)
	
	@blocked
	def add_class(self, cls):
		
		return self.classes.add(cls)
	
	@blocked
	def del_class(self, name):
		
		del self.classes[name]
	
	def to_dict(self):
		
		return dict(
			id = self.id,
			linked = self.linked,
			classes = self.classes._keys,
			relations = self.relations.to_dict(),
			descriptors = self.descriptors.to_dict(),
			**super(DObject, self).to_dict(),
		)
	
	def from_dict(self, data):
		
		self._classes = data["classes"]
		self._relations = data["relations"]
		self._descriptors = data["descriptors"]
	
	def from_dict_linked(self, data, identifier):
		
		self._classes = [(self.store.linked[identifier].prefix + "@" + name) for name in data["classes"]]
		
		self._relations = {}
		for rel in data["relations"]:
			self._relations[rel] = data["relations"][rel]
			self._relations[rel]["objects"] = [self.store.linked[identifier].object_lookup[id] for id in data["relations"][rel]["objects"]]
		
		self._descriptors = {}
		for name in data["descriptors"]:
			linked_name = self.store.linked[identifier].prefix + "@" + name
			self._descriptors[linked_name] = data["descriptors"][name]
			self._descriptors[linked_name]["target"] = self.store.linked[identifier].object_lookup[data["descriptors"][name]["target"]]
			self._descriptors[linked_name]["dclass"] = linked_name

