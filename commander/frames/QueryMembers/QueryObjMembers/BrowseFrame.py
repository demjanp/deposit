from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.LabelFrame import (LabelFrame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class BrowseFrame(Frame, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(6)
		self.setLayout(self.layout)
		
		self.label_frame = LabelFrame(self.model, self.view, self)
		self.layout.addWidget(self.label_frame)
		
		self.layout.addStretch()
		
		self.button_previous = QtWidgets.QToolButton()
		self.button_previous.setIcon(self.view.get_icon("previous_small.svg"))
		self.button_previous.setIconSize(QtCore.QSize(24, 24))
		self.button_previous.clicked.connect(self.on_previous)
		self.layout.addWidget(self.button_previous)
		
		self.button_next = QtWidgets.QToolButton()
		self.button_next.setIcon(self.view.get_icon("next_small.svg"))
		self.button_next.setIconSize(QtCore.QSize(24, 24))
		self.button_next.clicked.connect(self.on_next)
		self.layout.addWidget(self.button_next)
	
	def populate_data(self, obj):
		
		self.label_frame.populate_data(obj)
	
	def on_previous(self, *args):
		
		self.broadcast(Broadcasts.VIEW_BROWSE_PREVIOUS)
	
	def on_next(self, *args):
		
		self.broadcast(Broadcasts.VIEW_BROWSE_NEXT)

