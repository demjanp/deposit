from deposit import Broadcasts
from deposit.store.DLabel.DLabel import (DLabel)
from deposit.store.DLabel.DNone import (DNone)
from deposit.store.DElements.DElements import (DElement, DElements)
from deposit.store.DElements.DClasses import (DClass)
from deposit.store.Conversions import (as_url)
from deposit.store.Projections import (get_raster_projection)
from deposit.store.Worldfiles import (get_worldfile)

import os

class DDescriptor(DElement):
	
	def __init__(self, parent, cls, label):
		
		super(DDescriptor, self).__init__(parent)
		
		self.dclass = cls
		self.label = label
		self.geotag = None
		
	@property
	def target(self):
		# return target object
		
		if self.parent.__class__.__name__ == "DObject": # in case of null descriptor
			return self.parent
		return self.parent.parent
	
	@property
	def linked(self):
		
		return self.target.linked
	
	def to_dict(self):
		
		return dict(
			delement = "DDescriptor",
			target = self.target.id,
			dclass = self.dclass.name,
			label = self.label.to_dict(),
			geotag = self.geotag,
		)
	
	def __str__(self):
		
		return "DDescriptor: %s" % str(self.label)
	
	def __repr__(self):
		
		value = self.__str__()
		if not value is None:
			value = value.encode("utf-8")
		return value

class DDescriptors(DElements):
	
	def __init__(self, parent):
		
		super(DDescriptors, self).__init__(parent)
	
	def add(self, cls, label, dtype = "DString"):
		# cls = DClass or str
		# label = DLabel or other type (will be converted according to dtype)
		# dtype = DString / DDateTime / DResource / DGeometry / DNone
		# returns the set / created DDescriptor
		
		if cls.__class__.__name__ != "DClass":
			cls = self.store.classes.add(str(cls))

		del self[cls.name]

		if label is None:
			return

		if not isinstance(label, DLabel):
			if (dtype == "DResource") and (not self.store.local_folder is None):
				label = self.store.files.store_local(label)
				if label is None:
					raise Exception("Storing resource failed: %s" % (label.value))
			else:
				if dtype == "DResource":
					label = DLabel(as_url(label)).asdtype(dtype)
					format = self.store.images.get_format(label.value)
					if (format is None) and (not os.path.splitext(label.value)[1]):
						with label.open() as f:
							format = self.store.images.get_format(f)
					label.set_image((not format is None))
					if label.is_image():
						label.set_projection(get_raster_projection(label.value))
						label.set_worldfile(get_worldfile(label.value))
				else:
					label = DLabel(label).asdtype(dtype)
		
		self[cls.name] = DDescriptor(self, cls, label)
		for cls2 in self.parent.classes:
			self.parent.classes[cls2].add_descriptor(cls.name)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self.parent)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, cls)
		return self[cls.name]
	
	def rename(self, old_name, new_name):
		
		if old_name.__class__.__name__ == "DClass":
			old_name = old_name.name
		if old_name not in self:
			return
		if new_name.__class__.__name__ == "DClass":
			new_name = new_name.name
		if new_name not in self.store.classes:
			self.store.classes.add(new_name)
		self.add(new_name, self[old_name].label)
		del self[old_name]
	
	def _populate(self, key):
		
		descr = super(DDescriptors, self).__getitem__(key)
		if isinstance(descr, dict):
			label = DLabel("").asdtype(descr["label"]["dtype"]).from_dict(descr["label"])
			self[key] = DDescriptor(self, self.store.classes[descr["dclass"]], label)
			self[key].geotag = descr["geotag"]
	
	def __contains__(self, key):
		
		if super(DDescriptors, self).__contains__(key):
			self._populate(key)
			return True
		return False
	
	def __getitem__(self, key):
		
		if super(DDescriptors, self).__contains__(key):
			self._populate(key)
			return super(DDescriptors, self).__getitem__(key)
		return DDescriptor(self, DClass(self.store, "[no class]"), DNone())
	
	def __delitem__(self, name):

		if not name in self:
			return

		def delete_if_local():
			# if descriptor exists & it's a resource & the resource is not used by another descriptor, remove the resource

			for id in self.store.objects:
				for descr in self.store.objects[id].descriptors:
					descr2 = self.store.objects[id].descriptors[descr]
					if (descr2 != self[name]) and (descr2.label.__class__.__name__ == "DResource") and (descr2.label.value == self[name].label.value):
						return
			self.store.files.delete_local(self[name].label.value)

		if self[name].label.__class__.__name__ == "DResource":
			delete_if_local()
		
		dclass = self[name].dclass
		
		self.del_naive(name)

		self.broadcast(Broadcasts.ELEMENT_CHANGED, dclass)
		self.broadcast(Broadcasts.ELEMENT_CHANGED, self.parent)

	def update_order(self):
		
		self._keys = sorted(self._keys, key = lambda key: self[key].dclass.order)
	
	def to_dict(self):
		
		return dict([(name, self._members[name] if isinstance(self._members[name], dict) else self._members[name].to_dict()) for name in self._keys])
	
	def from_dict(self, data):
		
		for name in data:
			self.add_naive(name, data[name])
		return self
	
	def restore_dclasses(self):
		# to be run subsequently after classes are loaded
		
		for name in self:
			self[name].dclass = self.store.classes[self[name].dclass]

