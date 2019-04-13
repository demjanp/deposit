from deposit.commander.usertools import (DialogControls)

from PySide2 import (QtWidgets, QtCore, QtGui)

class DialogFrame(QtWidgets.QFrame):
	
	def __init__(self, model, user_control):
		# user_control = UserElement
		
		self.model = model
		self.user_control = user_control
		self.ctrl = None
		
		QtWidgets.QFrame.__init__(self)
		
		self.ctrl = getattr(DialogControls, user_control.__class__.__name__)(self.model, self.user_control)
		
		self.setLayout(QtWidgets.QFormLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
		label = QtWidgets.QLabel("%s:" % (self.user_control.label))
		label.setStyleSheet(self.user_control.stylesheet)
		self.layout().addRow(label, self.ctrl)
	
	@property
	def dclass(self):
		
		return self.user_control.dclass
	
	@property
	def descriptor(self):
		
		return self.user_control.descriptor
	
	def set_value(self, value):
		
		self.ctrl.set_value(value)
	
	def get_value(self):
		
		return self.ctrl.get_value()

