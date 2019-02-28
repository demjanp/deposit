
from PyQt5 import (QtWidgets, QtCore, QtGui)

class XLSXSheet(QtWidgets.QWidget):
	
	def __init__(self, header, body):
		
		self.header = header
		self.body = body
		
		QtWidgets.QWidget.__init__(self)
		
		self.verticalLayout = QtWidgets.QVBoxLayout()
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.verticalLayout.setSpacing(0)
		self.setLayout(self.verticalLayout)
		
		self.verticalLayout.addWidget(self.header)
		self.verticalLayout.addWidget(self.body)
		
		self.header.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.body.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.header.horizontalHeader().sectionResized.connect(self.on_sectionResized)

	def on_horizontalScroll(self, position):
		
		self.header.horizontalScrollBar().setSliderPosition(position)
		self.body.horizontalScrollBar().setSliderPosition(position)
		
	def on_sectionResized(self, index, oldSize, newSize):
		
		self.body.horizontalHeader().resizeSection(index, newSize)

