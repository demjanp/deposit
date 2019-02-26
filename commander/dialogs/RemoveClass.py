from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class RemoveClass(Dialog):
	
	def title(self):
		
		if len(self.class_names) > 1:
			return "Remove Classes"
		else:
			return "Remove Class"
	
	def set_up(self, class_names, parent_class):
		
		self.class_names = class_names
		self.parent_class = parent_class
		
		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		label1 = QtWidgets.QLabel("Remove the following class%s?" % ("es" if (len(self.class_names) > 1) else ""), self)
		label2 = QtWidgets.QLabel(", ".join(self.class_names), self)
		self.check_parent_only = QtWidgets.QCheckBox("Only remove Descriptor from the parent Class")
		
		if (len(self.class_names) == 1) and (self.parent_class is not None):
			self.check_parent_only.setChecked(True)
		else:
			self.check_parent_only.setEnabled(False)
		
		self.layout.addWidget(label1)
		self.layout.addWidget(label2)
		self.layout.addWidget(self.check_parent_only)
	
	def process(self):
		
		if self.check_parent_only.isChecked():
			self.model.classes[self.parent_class].del_descriptor(self.class_names[0])
		else:
			for cls in self.class_names:
				del self.model.classes[cls]
	
