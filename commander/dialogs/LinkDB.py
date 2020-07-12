from deposit.commander.dialogs._Dialog import (Dialog)
from deposit.store.Store import (Store)

from PySide2 import (QtWidgets, QtCore, QtGui)

class LinkDB(Dialog):
	
	def title(self):
		
		return "Link Database"
	
	def set_up(self):
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		self.temp_store = Store()
		self.db = self.temp_store.datasources.DB()
		self.dbrel = self.temp_store.datasources.DBRel()
		self.ds = None
		
		connstrings = []
		for row in self.view.menu.get_recent(): # [[url], [identifier, connstr], ...]
			if len(row) == 2:
				connstrings.append(row[1])
		
		self.connstr = QtWidgets.QComboBox()
		if connstrings:
			self.connstr.addItems(connstrings)
		self.connstr.setEditable(True)
		self.connstr.currentTextChanged.connect(self.on_connstr_changed)
		
		self.identifier = QtWidgets.QListWidget()
		
		self.form_layout.addRow("Connect string:", self.connstr)
		self.form_layout.addRow("Identifier:", self.identifier)
		
		if connstrings:
			self.on_connstr_changed(connstrings[0])
	
	def on_connstr_changed(self, connstr):
		
		self.identifier.clear()
		self.identifier.setEnabled(False)
		self.ds = None
		if connstr:
			if self.dbrel.set_connstr(connstr) and self.dbrel.is_valid():
				self.identifier.addItem(self.dbrel.get_identifier())
				self.ds = self.dbrel
				return
			
			if self.db.set_connstr(connstr):
				identifiers = self.db.get_identifiers()
				if identifiers:
					self.identifier.addItems(identifiers)
					self.identifier.setEnabled(True)
					self.ds = self.db
	
	def process(self):
		
		item = self.identifier.currentItem()
		if item and item.isSelected():
			identifier = item.text()
			if identifier and (not self.ds is None):
				if self.ds.identifier is None:
					self.ds.set_identifier(identifier)
				self.ds.link()
				self.view.menu.add_recent_db(self.ds.identifier, self.ds.connstr)
	
	