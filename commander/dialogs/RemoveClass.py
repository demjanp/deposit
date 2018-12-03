from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class RemoveClass(Dialog):
	
	def title(self):
		
		if len(self.class_names) > 1:
			return "Remove Classes"
		else:
			return "Remove Class"
	
	def set_up(self, class_names):
		
		self.class_names = class_names
		
		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		label1 = QtWidgets.QLabel("Remove the following class%s?" % ("es" if (len(self.class_names) > 1) else ""), self)
		label2 = QtWidgets.QLabel(", ".join(self.class_names), self)
		
		self.layout.addWidget(label1)
		self.layout.addWidget(label2)
	
	def process(self):
		
		for cls in self.class_names:
			del self.model.classes[cls]
	
