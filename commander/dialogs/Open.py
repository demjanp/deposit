
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs._Dialog import (Dialog)
from deposit.commander.dialogs.OpenMembers.OpenRecent import (OpenRecent)
from deposit.commander.dialogs.OpenMembers.OpenJSON import (OpenJSON)
from deposit.commander.dialogs.OpenMembers.OpenDB import (OpenDB)
from deposit.commander.dialogs.OpenMembers.OpenDBRel import (OpenDBRel)
from deposit.commander.dialogs.OpenMembers.OpenMemory import (OpenMemory)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class Open(Dialog):
	
	def title(self):
		
		return "Select Data Source"
	
	def set_up(self):
		
		self.setMinimumWidth(600)
		self.setMinimumHeight(400)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		self.tab_recent = OpenRecent(self.model, self.view, self)
		self.tab_json = OpenJSON(self.model, self.view, self)
		self.tab_db = OpenDB(self.model, self.view, self)
		self.tab_dbrel = OpenDBRel(self.model, self.view, self)
		self.tab_memory = OpenMemory(self.model, self.view, self)
		
		self.tabs = QtWidgets.QTabWidget()
		self.tabs.addTab(self.tab_recent, "Recent")
		self.tabs.addTab(self.tab_json, "File")
		self.tabs.addTab(self.tab_db, "PostgreSQL")
		self.tabs.addTab(self.tab_dbrel, "PostgreSQL Relational")
		self.tabs.addTab(self.tab_memory, "Memory")
		
		self.layout().addWidget(self.tabs)
	
	def button_box(self):
		
		return False, False
