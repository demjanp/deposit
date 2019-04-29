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
		
		return True
	
	def triggered(self, state):
		
		path = QtWidgets.QFileDialog.getExistingDirectory(self.view, caption = "Select Local Folder")
		if path:
			self.model.set_local_folder(os.path.normpath(os.path.abspath(path)))
			reply = QtWidgets.QMessageBox.question(self.view, "Localise Resources", "Move all resources to the Local Folder?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
			if reply == QtWidgets.QMessageBox.Yes:
				self.model.localise_resources()

