from deposit.commander.dialogs._Dialog import (Dialog)
from deposit.store.Conversions import (as_url)

from PySide2 import (QtWidgets, QtCore, QtGui)

class SaveAsDB(Dialog):
	
	def title(self):
		
		return "Save As Database"
	
	def set_up(self):

		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)

		connstrings = []
		for row in self.view.menu.get_recent():  # [[url], [identifier, connstr], ...]
			if len(row) == 2:
				connstrings.append(row[1])

		self.connstr = QtWidgets.QComboBox()
		if connstrings:
			self.connstr.addItems(connstrings)
		self.connstr.setEditable(True)

		self.identifier = QtWidgets.QComboBox()
		if self.model.identifier:
			self.identifier.addItems([self.model.identifier])
		
		if self.model.data_source.__class__.__name__ == "DB":
			identifiers = self.model.data_source.get_identifiers()
			if identifiers:
				self.identifier.addItems(identifiers)
		
		self.identifier.setEditable(True)

		self.form_layout.addRow("Connect string:", self.connstr)
		self.form_layout.addRow("Identifier:", self.identifier)

	def process(self):

		connstr = self.connstr.currentText()
		identifier = self.identifier.currentText()
		if connstr and identifier:
			identifier = as_url(identifier)
			ds = self.model.datasources.DB(identifier = identifier, connstr = connstr)
			cursor, _ = ds.connect()
			if cursor:
				self.model.set_datasource(ds)
				self.view.save()

