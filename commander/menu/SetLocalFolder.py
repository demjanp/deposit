from deposit.commander.toolbar._Tool import (Tool)
from PySide2 import (QtWidgets)
import os

class SetLocalFolder(Tool):
	
	def name(self):
		
		return "Set Local Folder"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Set Local Folder"
	
	def enabled(self):
		
		return (self.model.data_source is not None) and (self.model.data_source.name not in ["JSON", "Pickle"])
	
	def triggered(self, state):
		
		path = QtWidgets.QFileDialog.getExistingDirectory(self.view, caption = "Select Local Folder")
		if path:
			self.model.set_local_folder(os.path.normpath(os.path.abspath(path)))

