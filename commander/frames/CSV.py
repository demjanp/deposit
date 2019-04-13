from deposit import Broadcasts
from deposit.commander.frames.External.External import External
from deposit.commander.frames.External.ExternalHeader import ExternalHeader
from deposit.commander.frames.External.ExternalLst import ExternalLst

from PySide2 import (QtWidgets, QtCore, QtGui)

class CSV(External, QtWidgets.QWidget):

	def __init__(self, model, view, parent, es):
		
		External.__init__(self, model, view, parent, es)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):

		self.verticalLayout = QtWidgets.QVBoxLayout()
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.verticalLayout.setSpacing(0)
		self.setLayout(self.verticalLayout)
		
		self.header = ExternalHeader(self, self.es)
		self.body = ExternalLst(self, self.es)
		
		self.verticalLayout.addWidget(self.header)
		self.verticalLayout.addWidget(self.body)
		
		self.header.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.body.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.header.horizontalHeader().sectionResized.connect(self.on_sectionResized)

	def name(self):
		
		return self.es.url
	
	def icon(self):
		
		return "xlsxfile.svg"
	
	def on_horizontalScroll(self, position):
		
		self.header.horizontalScrollBar().setSliderPosition(position)
		self.body.horizontalScrollBar().setSliderPosition(position)
		
	def on_sectionResized(self, index, oldSize, newSize):
		
		self.body.horizontalHeader().resizeSection(index, newSize)

