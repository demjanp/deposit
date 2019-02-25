
from deposit import Broadcasts
from deposit.store.DElements.DElements import (DElement, DElements)
from deposit import (INVALID_CHARACTERS_NAME)

from numbers import Number

class DRelation(DElement):
	
	def __init__(self, parent, name):
		
		super(DRelation, self).__init__(parent)
		
		self.name = name
		self._objects = None
		self._weights = {}  # {id: weight, ...}
	
	@property
	def source(self):
		# return source object
		
		return self.parent.parent
	
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
				raise Exception("DRelation._objects is wrong type:", type(self._objects))
			self._objects.set_on_added(self.on_object_added)
			self._objects.set_on_deleted(self.on_object_deleted)

		return self._objects
	
	def weight(self, target_id):
		
		if target_id.__class__.__name__ == "DObject":
			target_id = target_id.id
		if target_id in self._weights:
			return self._weights[target_id]
		return None
	
	def _set_weight(self, target_id, weight):
		
		if target_id.__class__.__name__ == "DObject":
			target_id = target_id.id
		self._weights[target_id] = weight
		
	
	def set_weight(self, target_id, weight):
		
		self._set_weight(target_id, weight)
		self.store.objects[target_id].relations[self.store.reverse_relation(self.name)]._set_weight(self.source.id, weight)
	
	def on_object_added(self, obj):

		self.broadcast(Broadcasts.ELEMENT_CHANGED, self.source)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, obj)

	def on_object_deleted(self, obj):

		if obj.id in self._weights:
			del self._weights[obj.id]
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self.source)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, obj)

	def keys(self):
		
		return self.objects.keys()
	
	def __len__(self):
		
		return len(self.objects)
	
	def __contains__(self, key):
		
		return key in self.objects
	
	def __getitem__(self, key):
		
		return self.objects[key]
	
	def __setitem__(self, key, member):
		
		self.objects[key] = member
	
	def __iter__(self):
		
		for key in self.objects.keys():
			yield key
	
	def __next__(self):
		
		self.objects.__next__()
	
	def __delitem__(self, key):

		if key in self.objects:
			rev_name = self.store.reverse_relation(self.name)
			del self.objects[key].relations[rev_name].objects[self.source.id]
			if not len(self.objects[key].relations[rev_name]):
				del self.objects[key].relations[rev_name]
			del self.objects[key]
			if not len(self.objects):
				del self.source.relations[self.name]
	
	def to_dict(self):
		
		return dict(
			delement = "DRelation",
			name = self.name,
			objects = self.objects._keys,
			weights = self._weights.copy(),
		)
	
	def from_dict(self, data):
		
		self._objects = data["objects"]
		self._weights = data["weights"] if "weights" in data else {}  # DEBUG to ensure compatibility with previous version
		return self

class DRelations(DElements):
	
	def __init__(self, parent):
		
		super(DRelations, self).__init__(parent)
		
	def _add(self, name, target, weight):
		# target = DObject or id
		
		if target.__class__.__name__ != "DObject":
			target = self.store.objects[target]
		if not name in self:
			self[name] = DRelation(self, name)
			for class_name1 in self.parent.classes:
				if len(target.classes):
					for class_name2 in target.classes:
						self.store.classes[class_name1].add_relation(name, class_name2)
				else:
					self.store.classes[class_name1].add_relation(name, "!*")
		self[name][target.id] = target
		if isinstance(weight, Number):
			self[name]._set_weight(target.id, weight)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self.parent)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, target)
		return target
	
	def add(self, name, target, weight = None):
		# target = DObject or id
		# returns the created DRelation
		
		for char in INVALID_CHARACTERS_NAME:
			if char in name:
				raise Exception("Invalid character (%s) in Relation name" % (char))
		target = self._add(name, target, weight)
		target.relations._add(self.store.reverse_relation(name), self.parent, weight)
		return self[name]
	
	def _populate(self, key):
		
		rel = super(DRelations, self).__getitem__(key)
		if isinstance(rel, dict):
			self[key] = DRelation(self, key).from_dict(rel)
	
	def __contains__(self, key):
		
		if super(DRelations, self).__contains__(key):
			self._populate(key)
			return True
		return False
	
	def __getitem__(self, key):
		
		if super(DRelations, self).__contains__(key):
			self._populate(key)
			return super(DRelations, self).__getitem__(key)
		return DRelation(self, None)
	
	def __delitem__(self, name):
		
		if name in self:
			for id in self[name]:
				del self[name][id]
			self.del_naive(name)
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self.parent)

	def to_dict(self):
		
		return dict([(name, self._members[name] if isinstance(self._members[name], dict) else self._members[name].to_dict()) for name in self._keys])
	
	def from_dict(self, data):
		
		for name in data:
			self.add_naive(name, data[name])
		return self

