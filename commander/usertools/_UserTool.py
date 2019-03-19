
from PyQt5 import (QtWidgets, QtCore, QtGui)

class UserTool(QtWidgets.QAction):
	
	def __init__(self, label, view):
		
		self.label = label
		
		QtWidgets.QAction.__init__(self, view)
		
		self.setText(self.label)
		self.setToolTip(self.label)
		self.triggered.connect(self.on_triggered)
	
	def on_triggered(self, state):
		
		pass
	
	def to_dict(self):
		
		return dict(
			typ = self.__class__.__name__,
			label = self.label,
		)

