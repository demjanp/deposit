
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs._Dialog import (Dialog)
from deposit.commander.dialogs.DataSourceMembers.DataSourceRecent import (DataSourceRecent)
from deposit.commander.dialogs.DataSourceMembers.DataSourceJSON import (DataSourceJSON)
from deposit.commander.dialogs.DataSourceMembers.DataSourceDB import (DataSourceDB)
from deposit.commander.dialogs.DataSourceMembers.DataSourceDBRel import (DataSourceDBRel)
from deposit.commander.dialogs.DataSourceMembers.DataSourceMemory import (DataSourceMemory)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class DataSource(Dialog):
	
	def title(self):
		
		return "Select Data Source"
	
	def set_up(self):
		
		self.setMinimumWidth(600)
		self.setMinimumHeight(400)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		self.tab_recent = DataSourceRecent(self.model, self.view, self)
		self.tab_json = DataSourceJSON(self.model, self.view, self)
		self.tab_db = DataSourceDB(self.model, self.view, self)
		self.tab_dbrel = DataSourceDBRel(self.model, self.view, self)
		
		self.tabs = QtWidgets.QTabWidget()
		self.tabs.addTab(self.tab_recent, "Recent")
		self.tabs.addTab(self.tab_json, "File")
		self.tabs.addTab(self.tab_db, "PostgreSQL")
		self.tabs.addTab(self.tab_dbrel, "PostgreSQL Relational")
		if self.creating_enabled():
			self.tab_memory = DataSourceMemory(self.model, self.view, self)
			self.tabs.addTab(self.tab_memory, "Memory")
		
		self.layout().addWidget(self.tabs)
		if not self.tab_recent.has_items():
			self.tabs.setCurrentIndex(1)
	
	def button_box(self):
		
		return False, False
		
	def creating_enabled(self):
		
		return False
	
	def connect_caption(self):
		
		return "Connect"
	
	def logo(self):
		
		return None
	
	def on_connect(self, datasource, local_folder = None, created = False):
		
		self.close()

