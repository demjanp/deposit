from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class RenameClass(Dialog):

	def title(self):

		return "Rename Class"

	def set_up(self, class_name, parent_class):
		
		self.class_name = class_name
		self.parent_class = parent_class
		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		self.name = QtWidgets.QLineEdit(self.class_name)
		self.check_parent_only = QtWidgets.QCheckBox("Only rename Descriptor of the parent Class")
		self.form_layout.addRow("Name:", self.name)
		self.form_layout.addRow(self.check_parent_only)
		
		self.check_parent_only.setEnabled(self.parent_class is not None)

	def process(self):

		new_name = self.name.text()
		if new_name and (new_name != self.class_name):
			if self.check_parent_only.isChecked():
				self.model.classes[self.parent_class].rename_descriptor(self.class_name, new_name)
			else:
				self.model.classes.rename(self.class_name, new_name)

