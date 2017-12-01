from deposit.commander.PrototypeExternalModel import PrototypeExternalModel
import os

class XLSXWorkbookModel(PrototypeExternalModel):

	def __init__(self, parent_model, uri, sheet = None):
		
		self._sheet = sheet
		self._sheets = [] # [sheet, ...]
		self._filename = os.path.split(uri)[-1]
		
		super(XLSXWorkbookModel, self).__init__(parent_model, uri)
		
		path, filename, storage_type = self._parent_model.store.resources.get_path(uri)
		if not storage_type in [self._parent_model.store.resources.RESOURCE_STORED, self._parent_model.store.resources.RESOURCE_LOCAL, self._parent_model.store.resources.RESOURCE_CONNECTED_LOCAL]:
			raise NotImplementedError # TODO support remotely stored files		
		if sheet is None:
			self._sheets = self._parent_model.store.file.xlsx.get_sheets(path)
		else:
			fields, data = self._parent_model.store.file.xlsx.get_sheet(path, sheet)
			self.set_data(data, fields)
	
	def sheet(self):
		
		return self._sheet
	
	def sheets(self):
		# return [sheet, ...]
		
		return self._sheets
	
	def filename(self):
		
		return self._filename
	
	