from deposit.commander.toolbar._Tool import (Tool)
from deposit.commander.frames.External.External import External

from PySide2 import (QtWidgets, QtCore, QtGui)

class Import(Tool):
	
	def name(self):
		
		return "Import External"
	
	def icon(self):
		
		return "import.svg"
	
	def help(self):
		
		return "Import External Data"
	
	def enabled(self):

		return isinstance(self.view.mdiarea.get_current(), External)
	
	def triggered(self, state):
		
		self.view.dialogs.open("Import", self.view.mdiarea.get_current())

