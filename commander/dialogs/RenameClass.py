from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class RenameClass(Dialog):

	def title(self):

		return "Rename Class"

	def set_up(self, class_name):

		self.class_name = class_name
		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)

		self.name = QtWidgets.QLineEdit(self.class_name)
		self.form_layout.addRow("Name:", self.name)

	def process(self):

		new_name = self.name.text()
		if new_name and (new_name != self.class_name):
			self.model.classes.rename(self.class_name, new_name)

