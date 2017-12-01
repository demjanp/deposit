from deposit.commander.PrototypeExternalModel import PrototypeExternalModel
from deposit.DLabel import (DGeometry, DString)
import os

class ShapefileModel(PrototypeExternalModel):
	
	def __init__(self, parent_model, uri):
		
		self._filename = os.path.split(uri)[-1]
		
		super(ShapefileModel, self).__init__(parent_model, uri)
		
		path, filename, storage_type = self._parent_model.store.resources.get_path(uri)
		if not storage_type in [self._parent_model.store.resources.RESOURCE_STORED, self._parent_model.store.resources.RESOURCE_LOCAL, self._parent_model.store.resources.RESOURCE_CONNECTED_LOCAL]:
			raise NotImplementedError # TODO support remotely stored files
		geometries, srid, fields, data = self._parent_model.store.file.shapefiles.get_data(path)
		self.set_data(data, fields, geometries, srid)
	
	def filename(self):
		
		return self._filename
	