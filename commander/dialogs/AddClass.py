from deposit import Broadcasts
from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class AddClass(Dialog):
	
	def title(self):
		
		if self.obj is None:
			return "Add Class"
		return "Add Object to Class"
	
	def set_up(self, obj = None):
		
		self.obj = obj
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		if self.obj is None:
			self.name = QtWidgets.QLineEdit()
		else:
			self.name = QtWidgets.QComboBox()
			if isinstance(self.obj, list):
				self.name.addItems(self.model.classes.keys())
			else:
				self.name.addItems([name for name in self.model.classes if not name in self.obj.classes])
			self.name.setEditable(True)
		
		self.form_layout.addRow("Name:", self.name)
	
	def process(self):
		
		if hasattr(self.name, "text"):
			name = self.name.text()
		else:
			name = self.name.currentText()
		if name:
			if self.obj is None:
				self.model.classes.add(name)
			elif isinstance(self.obj, list):
				for obj in self.obj:
					obj.classes.add(name)
			else:
				self.obj.classes.add(name)
	
