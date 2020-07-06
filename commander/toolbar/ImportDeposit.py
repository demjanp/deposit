from deposit.commander.toolbar._Tool import (Tool)

from PySide2 import (QtWidgets, QtCore, QtGui)

class ImportDeposit(Tool):
	
	def name(self):
		
		return "Import Deposit Database"
	
	def icon(self):
		
		return "import_deposit.svg"
	
	def help(self):
		
		return "Import a Deposit Database"
	
	def enabled(self):

		return True
	
	def triggered(self, state):
		
		self.view.dialogs.open("ImportDeposit")

