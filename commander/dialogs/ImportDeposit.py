
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs.DataSource import (DataSource)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class ImportDeposit(DataSource):
	
	def title(self):
		
		return "Select Deposit Database to Import"
	
	def creating_enabled(self):
		
		return False
	
	def connect_caption(self):
		
		return "Import"
		
	def on_connect(self, identifier, connstr, local_folder = None, created = False):
		
		if identifier is None:
			self.close()
			return
		self.model.add_objects(identifier, connstr)
		self.close()
