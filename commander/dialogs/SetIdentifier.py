from deposit.commander.dialogs._Dialog import (Dialog)
from deposit.commander.toolbar.Save import (Save)

from PySide2 import (QtWidgets, QtCore, QtGui)

class SetIdentifier(Dialog):
	
	def title(self):
		
		return "Set Identifier"
	
	def set_up(self, save = False):
		
		self.save = save
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		self.identifier = QtWidgets.QComboBox()
		if self.model.identifier:
			self.identifier.addItems([self.model.identifier])
		
		if self.model.data_source.__class__.__name__ == "DB":
			identifiers = self.model.data_source.get_identifiers()
			if identifiers:
				self.identifier.addItems(identifiers)
		
		self.identifier.setEditable(True)
		
		self.form_layout.addRow("Identifier:", self.identifier)
	
	def process(self):
		
		identifier = self.identifier.currentText()
		if identifier:
			self.model.data_source.set_identifier(identifier)
			if self.save:
				self.save = Save(self.model, self.view)
				self.save.triggered(True)
				

