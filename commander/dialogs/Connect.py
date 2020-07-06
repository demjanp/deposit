
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs.DataSource import (DataSource)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class Connect(DataSource):
	
	def title(self):
		
		return "Select Data Source"
	
	def creating_enabled(self):
		
		return True

	def on_connect(self, identifier, connstr, local_folder = None, created = False):
		
		if identifier is None:
			self.model.clear()
			self.model.set_datasource(None)
		else:
			self.model.load(identifier, connstr)
			if local_folder:
				if created:
					self.model.set_local_folder(local_folder)
				elif self.model.local_folder != local_folder:
					reply = QtWidgets.QMessageBox.question(self, "Change Local Folder?", "Change Local Folder from %s to %s?" % (self.model.local_folder, local_folder), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
					if reply == QtWidgets.QMessageBox.Yes:
						self.model.set_local_folder(local_folder)
		self.close()

