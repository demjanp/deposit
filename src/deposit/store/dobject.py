from deposit.store.abstract_delement import AbstractDElement
from deposit.store.ddatetime import DDateTime
from deposit.store.dgeometry import DGeometry
from deposit.store.dresource import DResource

from deposit.utils.fnc_geometry import (coords_to_wkt, wkt_to_coords)

class DObject(AbstractDElement):
	
	def __init__(self, store, obj_id):
		
		AbstractDElement.__init__(self, store)
		
		self.id = obj_id
		
		self._descriptors = {}  # {DClass: value, ...}
		self._locations = {}  # {DClass: DGeometry, ...}
		self._json_descriptors = None
		self._json_locations = None
	
	def _on_class_deleted(self, cls):
		
		if cls in self._descriptors:
			del self._descriptors[cls]
			self._store.callback_changed([self])
			return True
		return False
	
	def to_dict(self):
		
		from deposit.utils.fnc_serialize import (dtype_to_dict)
		
		descriptors = dict([(descr.name, dtype_to_dict(self._descriptors[descr])) for descr in self._descriptors])
		locations = dict([(descr.name, self._locations[descr].to_dict()) for descr in self._locations])
		data = {}
		if descriptors:
			data["descriptors"] = descriptors
		if locations:
			data["locations"] = locations
		
		return data
	
	def from_dict_1(self, data):
		
		self._json_descriptors = data.get("descriptors", {})
		self._json_locations = data.get("locations", {})
		
		for name in self._json_descriptors:
			value = self._json_descriptors[name]
			if isinstance(value, dict) and (value["dtype"] == "DResource"):
				url, filename, is_stored, is_image = value["value"]
				self._json_descriptors[name] = self._store.add_resource(url, filename, is_stored, is_image)
				self._json_descriptors[name].add_object(self.id)
		
		return self
	
	def from_dict_2(self):
		
		from deposit.utils.fnc_serialize import (value_to_dtype)
		
		for name in self._json_descriptors:
			self._descriptors[self._store.get_class(name)] = value_to_dtype(self._json_descriptors[name])
		self._json_descriptors = None
		for name in self._json_locations:
			self._locations[self._store.get_class(name)] = DGeometry().from_dict(self._json_locations[name])
		self._json_locations = None
	
	
	# ---- Descriptors -------------------------------------------------------
	def set_descriptor(self, name, value):
		
		if value == self.get_descriptor(name):
			return
		self.del_descriptor(name)
		if value is None:
			return
		descr = self._store.add_class(name)
		self._descriptors[descr] = value
		if isinstance(value, DResource):
			self._descriptors[descr].add_object(self.id)
		for cls in self.get_classes():
			cls.set_descriptor(name)
		self._store._on_descriptor_set(descr)
		self._store.callback_changed([self])
	
	def set_resource_descriptor(
		self, name, url, filename = None, is_stored = None, is_image = None
	):
		# filename = "name.ext"; if None, determine automatically
		# is_stored = True if resource is stored in local folder
		#	= False, not stored locally
		#	= None, attempt to store it locally if possible & set is_stored flag
		# is_image = True if resource is an image; if None, determine automatically
		
		value = self._store.add_resource(url, filename, is_stored, is_image)
		value.add_object(self.id)
		self.set_descriptor(name, value)
	
	def set_geometry_descriptor(
		self, name, geometry_type, coords, srid = None, srid_vertical = None
	):
		# geometry_type = str (POINT / MULTIPOINT / LINESTRING / POLYGON / MULTIPOLYGON / POINTZ etc. / POINTM etc.)
		# coords = POINT: [x,y]
		# 	POINTZ: [x, y, z] etc.
		#	POINTM: [x, y, z, m] etc.
		#	MULTIPOINT / LINESTRING: [[x, y], ...]
		#	POLYGON: [exterior, hole1, hole2, ...]; exterior / hole = [[x, y], ...]
		#	MULTIPOLYGON: [POLYGON, ...]
		
		self.set_descriptor(name, DGeometry((geometry_type, coords, srid, srid_vertical)))
	
	def set_datetime_descriptor(self, name, value):
		# value = datetime.datetime or str in ISO format
		
		self.set_descriptor(name, DDateTime(value))
	
	def get_descriptor(self, name, default = None):
		
		descr = self._store.get_class(name)
		if descr is None:
			return default
		if descr in self._descriptors:
			return self._descriptors[descr]
		return default
	
	def has_descriptors(self):
		
		return len(self._descriptors) > 0
	
	def has_descriptor(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return False
		return (descr in self._descriptors)
	
	def get_descriptors(self, ordered = False):
		
		if ordered:
			return sorted(list(self._descriptors.keys()), key = lambda descr: descr.order)
		return list(self._descriptors.keys())
	
	def get_descriptor_names(self, ordered = False):
		
		return [descr.name for descr in self.get_descriptors(ordered)]
	
	def rename_rescriptor(self, name, new_name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return
		if descr not in self._descriptors:
			return
		value = self._descriptors[descr]
		del self._descriptors[descr]
		descr = self._store.add_class(new_name)
		self._descriptors[descr] = value
		for cls in self.get_classes():
			cls.set_descriptor(new_name)
		self._store._on_descriptor_deleted()
		self._store.callback_changed([self])
	
	def del_descriptor(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return
		if descr in self._descriptors:
			resource = None
			if isinstance(self._descriptors[descr], DResource):
				resource = self._descriptors[descr]
			del self._descriptors[descr]
			if descr in self._locations:
				del self._locations[descr]
			self._store._on_descriptor_deleted()
			if (resource is not None) and (resource not in self._descriptors.values()):
				resource.del_object(self.id)
				self._store._on_resource_deleted(resource)
			self._store.callback_changed([self])
	
	
	# ---- Locations ---------------------------------------------------------
	def set_location(self, name, value):
		# set location of the object on an image resource by a geometric shape ([0,0] being the bottom-left corner)
		# value = DGeometry
		#	WKT or 
		# 	(geometry_type, coords, srid, srid_vertical) or
		#	(geometry_type, coords, srid) or
		#	(geometry_type, coords)
		
		if value is None:
			self.del_location(name)
			return
		descr = self._store.add_class(name)
		if descr not in self._descriptors:
			raise Exception("Could not set location. Descriptor %s of Object %d does not exist" % (name, self.id))
		self._locations[descr] = DGeometry(value)
		self._store.callback_changed([self])
	
	def get_location(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return None
		if descr in self._locations:
			return self._locations[descr]
		return None
	
	def del_location(self, name):
		
		descr = self._store.get_class(name)
		if descr is None:
			return
		if descr in self._locations:
			del self._locations[descr]
			self._store.callback_changed([self])
	
	
	# ---- Classes -----------------------------------------------------------
	def get_classes(self, ordered = False, superclasses = False):
		# returns [DClass, ...]
		
		classes = set()
		if superclasses:
			for src in self._store.G.iter_class_ancestors(self.id):
				if isinstance(src, str):
					classes.add(self._store.G.get_class_data(src))
		else:
			for src in self._store.G.iter_class_parents(self.id):
				classes.add(self._store.G.get_class_data(src))
		
		if ordered:
			return sorted(list(classes), key = lambda cls: cls.order)
		return list(classes)
	
	def get_class_names(self, ordered = False, superclasses = False):
		# returns [name, ...]
		
		return [cls.name for cls in self.get_classes(ordered, superclasses)]
	
	def has_class(self, name = None):
		
		if name.__class__.__name__ == "DClass":
			name = name.name
		
		for src in self._store.G.iter_class_parents(self.id):
			if name is None:
				return True
			if src == name:
				return True
		return False
	
	
	# ---- Relations ---------------------------------------------------------
	def add_relation(self, obj_id_tgt, label, weight = None):
		
		if isinstance(obj_id_tgt, DObject):
			obj_id_tgt = obj_id_tgt.id
		self._store.check_obj_id(obj_id_tgt)
		obj_id_src = self.id
		obj_id_src, obj_id_tgt, label = self._store._check_inverse_rel(obj_id_src, obj_id_tgt, label)
		self._store.G.add_object_relation(obj_id_src, obj_id_tgt, label, weight)
		self._store.G.add_object_relation(obj_id_tgt, obj_id_src, "~" + label, weight)
		self._store._on_relation_added(label)
		obj = self._store.G.get_object_data(obj_id_tgt)
		self._store.callback_changed([self, obj])
	
	def has_relation(self, obj_id_tgt, label, chained = False):
		
		if isinstance(obj_id_tgt, DObject):
			obj_id_tgt = obj_id_tgt.id
		return self._store.G.has_object_relation(self.id, obj_id_tgt, label, chained)
	
	def get_relations(self, obj_id_tgt = None):
		# returns [(DObject, label), ...]
		
		if isinstance(obj_id_tgt, DObject):
			obj_id_tgt = obj_id_tgt.id
		
		for tgt, label in self._store.G.iter_object_relations(self.id):
			if (obj_id_tgt is not None) and (tgt != obj_id_tgt):
				continue
			yield (self._store.G.get_object_data(tgt), label)
	
	def get_relation_weight(self, obj_id_tgt, label):
		
		if isinstance(obj_id_tgt, DObject):
			obj_id_tgt = obj_id_tgt.id
		if self._store.G.has_object_relation(self.id, obj_id_tgt, label):
			return self._store.G.get_object_relation_weight(self.id, obj_id_tgt, label)
		return None
	
	def del_relation(self, obj_id_tgt, label):
		
		if isinstance(obj_id_tgt, DObject):
			obj_id_tgt = obj_id_tgt.id
		obj_id_src = self.id
		obj_id_src, obj_id_tgt, label = self._store._check_inverse_rel(obj_id_src, obj_id_tgt, label)
		
		if self._store.G.has_object_relation(obj_id_src, obj_id_tgt, label):
			self._store.G.del_object_relation(obj_id_src, obj_id_tgt, label)
			self._store.G.del_object_relation(obj_id_tgt, obj_id_src, "~" + label)
			self._store._on_relation_deleted()
			obj = self._store.G.get_object_data(obj_id_tgt)
			self._store.callback_changed([self, obj])
	
	
	def __repr__(self):
		
		return "DObject(%d)" % (self.id)

