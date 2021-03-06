from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.ViewChild import (ViewChild)

from deposit.commander.dialogs.AddClass import (AddClass)
from deposit.commander.dialogs.AddDescriptor import (AddDescriptor)
from deposit.commander.dialogs.AddRelation import (AddRelation)
from deposit.commander.dialogs.Connect import (Connect)
from deposit.commander.dialogs.LinkDB import (LinkDB)
from deposit.commander.dialogs.RemoveClass import (RemoveClass)
from deposit.commander.dialogs.RemoveObject import (RemoveObject)
from deposit.commander.dialogs.RemoveObjectsFromClass import (RemoveObjectsFromClass)
from deposit.commander.dialogs.RemoveRelation import (RemoveRelation)
from deposit.commander.dialogs.RenameClass import (RenameClass)
from deposit.commander.dialogs.Import import (Import)
from deposit.commander.dialogs.About import (About)
from deposit.commander.dialogs.AddQuery import (AddQuery)
from deposit.commander.dialogs.EditQuery import (EditQuery)
from deposit.commander.dialogs.OpenOrImport import (OpenOrImport)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Dialogs(CmdDict, ViewChild):
	
	def __init__(self, model, view):
		
		self.dialogs_open = []

		CmdDict.__init__(self, 
			AddClass, 
			AddDescriptor, 
			AddRelation, 
			Connect, 
			LinkDB, 
			RemoveClass, 
			RemoveObject, 
			RemoveObjectsFromClass, 
			RemoveRelation, 
			RenameClass, 
			Import, 
			About, 
			AddQuery, 
			EditQuery, 
			OpenOrImport, 
		)
		ViewChild.__init__(self, model, view)
		
		self.set_up()
	
	def set_up(self):
		
		pass
	
	def open(self, dialog_name, *args):
		
		if dialog_name in self.classes:
			dialog = self.classes[dialog_name](self.model, self.view, *args)
			self.dialogs_open.append(dialog_name)
			dialog.show()
			return dialog

	def is_open(self, dialog_name):
		
		return dialog_name in self.dialogs_open
	
	def on_finished(self, code, dialog):
		
		dialog.set_closed()
		
		self.dialogs_open.remove(dialog.__class__.__name__)
		
		if code == QtWidgets.QDialog.Accepted:	
			dialog.process()

