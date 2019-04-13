from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.ClassLabel import (ClassLabel)

from PySide2 import (QtWidgets, QtCore, QtGui)

class ClassesFrame(Frame, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.object = None
		self.class_labels = []
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addStretch()
		self.setLayout(self.layout)
	
	def populate_data(self, obj):
		
		self.object = obj
		
		self.clear_layout(self.layout)
		self.class_labels = []
		
		for cls in obj.classes:
			self.class_labels.append(ClassLabel(self.model, self.view, self, cls))
			self.layout.addWidget(self.class_labels[-1])
	
	def on_remove_class(self, name):
		
		del self.object.classes[name]
		
