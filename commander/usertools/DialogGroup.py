from deposit.commander.usertools.DialogFrame import (DialogFrame)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class DialogGroup(QtWidgets.QGroupBox):
	
	def __init__(self, model, user_group):
		# user_group = Group
		
		self.model = model
		self.user_group = user_group
		self.controls_frame = None
		
		QtWidgets.QGroupBox.__init__(self, self.user_group.label)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QVBoxLayout())
		self.controls_frame.layout().setContentsMargins(10, 10, 10, 10)
		self.layout().addWidget(self.controls_frame)
		
		for member in self.user_group.members:
			self.add_frame(member)
		
		self.setStyleSheet(self.user_group.stylesheet)
		
	def add_frame(self, user_control):
		
		self.controls_frame.layout().addWidget(DialogFrame(self.model, user_control))
		
	def frames(self):
		
		return list(self.controls_frame.findChildren(DialogFrame, options = QtCore.Qt.FindDirectChildrenOnly))

