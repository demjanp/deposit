from deposit import Broadcasts
from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class AddDescriptor(Dialog):
	
	def title(self):

		if self.is_objects:
			return "Add Descriptor to Object"
		else:
			return "Add Descriptor to Class"
	
	def set_up(self, objects_classes):
		
		self.objects_classes = objects_classes
		self.is_objects = (self.objects_classes[0].__class__.__name__ == "DObject")

		self.setMinimumWidth(600)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		self.name = QtWidgets.QComboBox()
		self.name.addItems(self.model.descriptor_names)
		self.name.setEditable(True)

		self.form_layout.addRow("Name:", self.name)

		if self.objects_classes[0].__class__.__name__ == "DObject":
			self.value = QtWidgets.QLineEdit()
			self.form_layout.addRow("Value:", self.value)
	
	def process(self):
		
		name = self.name.currentText()
		if name:
			if self.objects_classes[0].__class__.__name__ == "DObject":
				value = self.value.text()
				cls = None
				for obj in self.objects_classes:
					descr = obj.descriptors.add(name, value)
					cls = descr.dclass
			else:
				for cls in self.objects_classes:
					self.model.classes[cls].add_descriptor(name)

