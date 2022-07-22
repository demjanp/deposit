from deposit.store.abstract_delement import AbstractDElement

class DClass(AbstractDElement):
	
	def __init__(self, store, name, order):
		
		AbstractDElement.__init__(self, store)
		
		self.name = name
		self.order = order
		
		self._descriptors = set()
		self._json_descriptors = None
		
	
	def _on_class_deleted(self, cls):
		
		if cls in self._descriptors:
			self._descriptors.remove(cls)
			return True
		return False
	
	def to_dict(self):
		
		data = dict(
			order = self.order
		)
		descriptors = [descr.name for descr in self._descriptors]
		if descriptors:
			data["descriptors"] = descriptors
		
		return data
	
	def from_dict_1(self, data):
		
		self._json_descriptors = data.get("descriptors", [])
		
		return self
	
	def from_dict_2(self):
		
		for name in self._json_descriptors:
			self._descriptors.add(self._store.get_class(name))
		self._json_descriptors = None
	
	
	def rename(self, new_name):
		
		if isinstance(new_name, DClass):
			new_name = new_name.name
		if self._store.has_class(new_name):
			raise Exception("Cannot rename class %s to %s, as it already exists." % (self.name, new_name))
		self._store.G.rename_class(self.name, new_name)
		self.name = new_name
		self._store.callback_changed([self])
	
	
	def set_descriptor(self, name):
		
		descr = self._store.add_class(name)
		if descr in self._descriptors:
			return
		self._descriptors.add(descr)
		self._store._on_descriptor_set(descr)
		self._store.callback_changed([self])
	
	def has_descriptors(self):
		
		return len(self._descriptors) > 0
	
	def has_descriptor(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return False
		return (descr in self._descriptors)
	
	def del_descriptor(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return
		if descr in self._descriptors:
			self._descriptors.remove(descr)
			self._store._on_descriptor_deleted()
			self._store.callback_changed([self])
	
	def get_descriptors(self, ordered = False):
		
		if ordered:
			return sorted(list(self._descriptors), key = lambda descr: descr.order)
		return list(self._descriptors)
	
	def get_descriptor_names(self, ordered = False):
		
		return [descr.name for descr in self.get_descriptors(ordered)]
	
	def get_object_descriptor_names(self, ordered = False, direct_only = False):
		
		descriptors = set()
		for obj in self.get_members(direct_only = direct_only):
			descriptors.update(obj.get_descriptors())
		if ordered:
			return [descr.name for descr in sorted(list(descriptors), key = lambda descr: descr.order)]
		return [descr.name for descr in descriptors]
	
	def add_member(self, obj_id = None):
		# obj_id = int or DObject or None (will be created)
		#
		# returns DObject
		
		if obj_id is None:
			obj_id = self._store.add_object().id
		elif obj_id.__class__.__name__ == "DObject":
			obj_id = obj_id.id
		self._store.check_obj_id(obj_id)
		self._store.G.add_class_child(self.name, obj_id)
		obj = self._store.G.get_object_data(obj_id)
		for descr in obj.get_descriptors():
			self.set_descriptor(descr)
		self._store.callback_changed([self, obj])
		
		return obj
	
	def get_members(self, direct_only = False):
		# direct_only = if True, don't return members of subclasses
		#
		# returns set([DObject, ...])
		
		objects = set()
		if direct_only:
			tgts = list(self._store.G.iter_class_children(self.name))
		else:
			tgts = list(self._store.G.iter_class_descendants(self.name))
		for tgt in tgts:
			if isinstance(tgt, int):
				objects.add(self._store.G.get_object_data(tgt))
		
		return objects
	
	def del_member(self, obj_id):
		
		if obj_id.__class__.__name__ == "DObject":
			obj_id = obj_id.id
		if self._store.G.has_class_child(self.name, obj_id):
			self._store.G.del_class_child(self.name, obj_id)
			obj = self._store.G.get_object_data(obj_id)
			self._store.callback_changed([self, obj])
	
	
	def add_subclass(self, name):
		
		if isinstance(name, DClass):
			name = name.name
		cls = self._store.add_class(name)
		self._store.G.add_class_child(self.name, name)
		self._store.callback_changed([self, cls])
		
		return cls
	
	def get_subclasses(self, ordered = False):
		# returns [DClass, ...]
		
		subclasses = set()
		for tgt in self._store.G.iter_class_descendants(self.name):
			if isinstance(tgt, str):
				subclasses.add(self._store.G.get_class_data(tgt))
		
		if ordered:
			return sorted(list(subclasses), key = lambda cls: cls.order)
		return list(subclasses)
	
	def get_superclasses(self, ordered = False, recursive = False):
		# returns [DClass, ...]
		
		superclasses = set()
		if recursive:
			for src in self._store.G.iter_class_ancestors(self.name):
				if isinstance(src, str):
					superclasses.add(self._store.G.get_class_data(src))
		else:
			for src in self._store.G.iter_class_parents(self.name):
				if isinstance(src, str):
					superclasses.add(self._store.G.get_class_data(src))
		
		if ordered:
			return sorted(list(superclasses), key = lambda cls: cls.order)
		return list(superclasses)
	
	def del_subclass(self, name):
		
		if isinstance(name, DClass):
			name = name.name
		if self._store.G.has_class_child(self.name, name):
			self._store.G.del_class_child(self.name, name)
			self._store.callback_changed([self, self._store.G.get_class_data(name)])
	
	
	def has_relation(self, name_tgt, label):
		
		if isinstance(name_tgt, DClass):
			name_tgt = name_tgt.name
		return self._store.G.has_class_relation(self.name, name_tgt, label)
	
	def add_relation(self, name_tgt, label):
		
		if isinstance(name_tgt, DClass):
			name_tgt = name_tgt.name
		name_src = self.name
		name_src, name_tgt, label = self._store._check_inverse_rel(name_src, name_tgt, label)
		self._store.G.add_class_relation(name_src, name_tgt, label)
		self._store.G.add_class_relation(name_tgt, name_src, "~" + label)
		self._store._on_relation_added(label)
		self._store.callback_changed([
			self._store.G.get_class_data(name_src),
			self._store.G.get_class_data(name_tgt),
		])
	
	def get_relations(self, name_tgt = None):
		# returns [(DClass, label), ...]
		
		if isinstance(name_tgt, DClass):
			name_tgt = name_tgt.name
		
		for tgt, label in self._store.G.iter_class_relations(self.name):
			if (name_tgt is not None) and (tgt != name_tgt):
				continue
			yield (self._store.G.get_class_data(tgt), label)
	
	def get_object_relations(self, class_tgt = None, direct_only = False):
		# get between objects of this class and other classes
		# returns {(DClass, label), ...}
		
		if isinstance(class_tgt, str):
			class_tgt = self._store.get_class(class_tgt)
		relations = set()
		for obj_src in self.get_members(direct_only = direct_only):
			for obj_tgt, label in obj_src.get_relations():
				classes_tgt = obj_tgt.get_classes()
				if class_tgt is not None:
					if class_tgt not in classes_tgt:
						continue
					relations.add((class_tgt, label))
				else:
					for cls in classes_tgt:
						relations.add((cls, label))
		
		return relations
	
	def del_relation(self, name_tgt, label):
		
		if isinstance(name_tgt, DClass):
			name_tgt = name_tgt.name
		name_src = self.name
		name_src, name_tgt, label = self._store._check_inverse_rel(name_src, name_tgt, label)
		
		if self._store.G.has_class_relation(name_src, name_tgt, label):
			self._store.G.del_class_relation(name_src, name_tgt, label)
			self._store.G.del_class_relation(name_tgt, name_src, "~" + label)
			self._store._on_relation_deleted()
			self._store.callback_changed([
				self._store.G.get_class_data(name_src),
				self._store.G.get_class_data(name_tgt),
			])
	
	def __repr__(self):
		
		return "DClass(%s)" % (self.name)

