from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)


class RemoveObjectsFromClass(Dialog):

	def title(self):

		return "Remove Objects from Class"

	def set_up(self, objects):

		self.objects = objects

		self.setMinimumWidth(400)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)

		class_names = []
		for obj in self.objects:
			for name in obj.classes:
				if not name in class_names:
					class_names.append(name)

		self.name = QtWidgets.QComboBox()
		self.name.addItems(class_names)
		self.name.setEditable(True)

		self.form_layout.addRow("Name:", self.name)

	def process(self):

		name = self.name.currentText()
		if name:
			for obj in self.objects:
				del obj.classes[name]

