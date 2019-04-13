from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.ObjectLabel import (ObjectLabel)

from PySide2 import (QtWidgets, QtCore, QtGui)

class ObjectFrame(Frame, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		self.object_label = ObjectLabel(self.model, self.view, self)
		self.layout.addWidget(self.object_label)
	
	def populate_data(self, obj):
		
		self.object_label.populate_data(obj)

