from deposit.commander.toolbar._Tool import (Tool)
from PySide2 import (QtWidgets)
import os

class LocaliseResources(Tool):
	
	def name(self):
		
		return "Localise Resources"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Move all resources to the Local Folder"
	
	def enabled(self):
		
		return self.model.local_folder is not None
	
	def triggered(self, state):
		
		reply = QtWidgets.QMessageBox.question(self.view, "Localise Resources", "Move all resources to the Local Folder?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			self.model.localise_resources()

