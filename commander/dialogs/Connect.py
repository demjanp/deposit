from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Connect(Dialog):
	
	def title(self):
		
		return "Connect to Database"
	
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
		for row in self.view.menu.get_recent(): # [[url], [identifier, connstr], ...]
			if len(row) == 2:
				connstrings.append(row[1])
		
		self.connstr = QtWidgets.QComboBox()
		if connstrings:
			self.connstr.addItems(connstrings)
		self.connstr.setEditable(True)
		
		self.form_layout.addRow("Connect string:", self.connstr)
	
	def process(self):
		
		connstr = self.connstr.currentText()
		if connstr:
			ds = self.model.datasources.DBRel(connstr = connstr)
			if ds.is_valid():
				self.model.set_datasource(ds)
				return
			
			ds = self.model.datasources.DB(connstr = connstr)
			if ds.is_valid():
				self.model.set_datasource(ds)
				return
	
	
	