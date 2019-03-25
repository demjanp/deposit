from deposit.commander.usertools.DialogFrame import (DialogFrame)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class DialogMultiGroup(QtWidgets.QGroupBox):
	
	def __init__(self, model, user_group):
		# user_group = MultiGroup
		
		self.model = model
		self.user_group = user_group
		self.controls_frame = None
		self._framesets = []
		
		QtWidgets.QGroupBox.__init__(self, self.user_group.label)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QVBoxLayout())
		self.layout().addWidget(self.controls_frame)
		
		button_frame = QtWidgets.QFrame()
		button_frame.setLayout(QtWidgets.QHBoxLayout())
		button_frame.layout().setContentsMargins(5, 5, 5, 5)
		button_frame.layout().addStretch()
		button_add = QtWidgets.QPushButton("Add Entry")
		button_add.clicked.connect(self.on_add_entry)
		button_frame.layout().addWidget(button_add)
		self.layout().addWidget(button_frame)
		
		self.add_entry()
	
	def add_frameset(self):
		
		self._framesets.append(QtWidgets.QFrame())
		self._framesets[-1].setLayout(QtWidgets.QVBoxLayout())
		self.controls_frame.layout().addWidget(self._framesets[-1])
		return self._framesets[-1]
	
	def framesets(self):
		# returns [[DialogFrame, ...], ...]
		
		return [list(frameset.findChildren(DialogFrame, options = QtCore.Qt.FindDirectChildrenOnly)) for frameset in self._framesets]
	
	def add_frame(self, user_control):
		
		self._framesets[-1].layout().addWidget(DialogFrame(self.model, user_control))
	
	def add_entry(self):
		
		if len(self._framesets) > 0:
			line = QtWidgets.QFrame()
			line.setFrameShape(QtWidgets.QFrame.HLine)
			line.setFrameShadow(QtWidgets.QFrame.Sunken)
			self.controls_frame.layout().addWidget(line)
		self.add_frameset()
		for member in self.user_group.members:
			self.add_frame(member)
		return list(self._framesets[-1].findChildren(DialogFrame, options = QtCore.Qt.FindDirectChildrenOnly))
	
	def clear(self):
		
		for frame in self.controls_frame.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
			if frame.__class__.__name__ != "QFrame":
				continue
			self.controls_frame.layout().removeWidget(frame)
			frame.setParent(None)
		self._framesets = []
		self.add_entry()
	
	def on_add_entry(self, *args):
	
		self.add_entry()

