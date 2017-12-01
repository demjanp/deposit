from deposit.commander.PrototypeListModel import PrototypeListModel
from deposit.DLabel import (DResource, DGeometry)

class DescriptorModel(PrototypeListModel):
	
	def __init__(self, parent_model, obj_id, rel_id):
		
		self._obj_id = obj_id
		self._rel_id = rel_id
		self._label = None
		
		super(DescriptorModel, self).__init__(parent_model)
		
		self._label = self._parent_model.store.get_label(self._rel_id)
		self._cls_id, _ = self._parent_model.store.relations.get_source_target(self._rel_id)
	
	def is_url_image(self, url):
		
		return self._parent_model.store.resources.is_external_image(url)
	
	def is_geometry(self):
		
		return isinstance(self._label, DGeometry)
	
	def is_3d(self):
		
		return self._parent_model.store.resources.is_3d(self._label.value)
	
	def path(self):
		# return path, filename, storage_type
		
		if not self.is_geometry():
			return self._parent_model.store.resources.get_path(self._label.label)
		return None, None, None
	
	def descriptor_name(self):
		
		return self._parent_model.store.get_label(self._cls_id)
	
	def geometry(self):
		# return coords, type; coords = [[x, y], ...]
		
		if self.is_geometry():
			return self._label.coords
		return None, None
	
	def geotags(self):
		# return [[obj_id, rel_id, cls_id, descriptor, coords, typ, srid], ...]
		# TODO handle srid_vertical
		
		ret = []
		for geotag, obj_id, rel_id, cls_id in self._parent_model.store.geotags.get_uri(self._label.value):
			coords, typ, srid, srid_vertical = self._parent_model.store.geometry.to_coords(geotag)
			ret.append([obj_id, rel_id, cls_id, self._parent_model.store.get_label(cls_id), coords, typ, srid])
		return ret
	
	def data(self):
		
		return dict(
			parent = self.__class__.__name__,
			data = dict(
				obj_id = self._obj_id,
				cls_id = self._cls_id,
				rel_id = self._rel_id,
				value = self._label.value,
			),
		)
	
	def remove_geotags(self, rel_ids):
		# rel_ids = [rel_id, ...]
		
		self._parent_model.store.begin_change()
		for rel_id in rel_ids:
			self._parent_model.store.geotags.remove(rel_id)
		self._parent_model.store.end_change()
		