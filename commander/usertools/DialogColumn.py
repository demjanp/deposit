
from PySide2 import (QtWidgets, QtCore, QtGui)

class DialogColumn(QtWidgets.QFrame):
	
	def __init__(self):
		
		QtWidgets.QFrame.__init__(self)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().addStretch()
		
#		self.setStyleSheet("DialogColumn {border: 1px solid gray;}")
	
	def add_widget(self, widget):
		
		self.layout().insertWidget(self.layout().count() - 1, widget)
