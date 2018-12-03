from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.ViewChild import (ViewChild)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class Dialogs(CmdDict, ViewChild):
	
	def __init__(self, model, view):
		
		self.dialogs_open = []

		CmdDict.__init__(self)
		ViewChild.__init__(self, model, view)
		
		self.set_up()
	
	def set_up(self):
		
		pass
	
	def open(self, dialog_name, *args):
		
		if dialog_name in self.classes:
			dialog = self.classes[dialog_name](self.model, self.view, *args)
			dialog.finished.connect(self.on_finished)
			self.dialogs_open.append(dialog_name)
			dialog.show()
		return dialog

	def is_open(self, dialog_name):
		
		return dialog_name in self.dialogs_open
	
	def on_finished(self, code):
		
		dialog = self.view.sender()
		
		dialog.set_closed()
		
		self.dialogs_open.remove(dialog.__class__.__name__)
		
		if code == QtWidgets.QDialog.Accepted:			
			dialog.process()
	