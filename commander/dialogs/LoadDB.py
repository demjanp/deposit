from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)
from collections import defaultdict

class LoadDB(Dialog):
	
	def title(self):
		
		return "Load Database"
	
	def set_up(self):
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		label = QtWidgets.QLabel("Connect string: %s" % (self.model.data_source.connstr))
		self.layout.addWidget(label)
		
		_, tables = self.model.data_source.connect()
		collect = defaultdict(list) # {identifier: [name, ...], ...}
		for table in tables:
			ident = table.split("#")
			if len(ident) == 2:
				ident, name = ident
				collect[ident].append(name)
		
		def is_deposit_db(names):
			
			for name in ["classes", "objects", "changed", "local_folder"]:
				if not name in names:
					return False
			return True
		
		identifiers = [ident + "#" for ident in collect if is_deposit_db(collect[ident])]
		
		self.identifier = QtWidgets.QListWidget()
		if identifiers:
			self.identifier.addItems(identifiers)
		
		self.layout.addWidget(self.identifier)
	
	def process(self):
		
		item = self.identifier.currentItem()
		if item.isSelected():
			identifier = item.text()
			if identifier:
				self.model.data_source.set_identifier(identifier)
				self.model.data_source.load()
				self.view.menu.add_recent_db(self.model.data_source.identifier, self.model.data_source.connstr)

