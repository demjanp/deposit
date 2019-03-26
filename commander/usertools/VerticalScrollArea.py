from PyQt5 import (QtWidgets, QtCore, QtGui)

class VerticalScrollArea(QtWidgets.QScrollArea):
	
	def __init__(self, contents):
		
		self.contents = contents
		
		QtWidgets.QScrollArea.__init__(self)
		
		self.setWidgetResizable(True)
		self.setFrameStyle(QtWidgets.QFrame.NoFrame)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.contents.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		self.setWidget(self.contents)
	
	def resizeEvent(self, event):
		
		self.contents.setMinimumWidth(self.width() - self.verticalScrollBar().width())

