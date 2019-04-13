from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.ObjectFrame import (ObjectFrame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.ClassesFrame import (ClassesFrame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class LabelFrame(Frame, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.object_frame = ObjectFrame(self.model, self.view, self)
		self.classes_frame = ClassesFrame(self.model, self.view, self)
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(1, 0, 0, 3)
		self.layout.addWidget(self.object_frame)
		self.layout.addWidget(self.classes_frame)
		self.setLayout(self.layout)
	
	def populate_data(self, obj):
		
		self.object_frame.populate_data(obj)
		self.classes_frame.populate_data(obj)
