from deposit.commander.toolbar._Tool import (Tool)
from deposit.commander.frames.External.External import External

from PySide2 import (QtWidgets, QtCore, QtGui)

class Import(Tool):
	
	def name(self):
		
		return "Import"
	
	def icon(self):
		
		return "import.svg"
	
	def help(self):
		
		return "Import Data"
	
	def enabled(self):

		return isinstance(self.view.mdiarea.get_current(), External)
	
	def triggered(self, state):
		
		reply = QtWidgets.QMessageBox.question(self.view, "Import Data", "Import into database?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
		if reply == QtWidgets.QMessageBox.Yes:
			current = self.view.mdiarea.get_current()
			current.import_data()

