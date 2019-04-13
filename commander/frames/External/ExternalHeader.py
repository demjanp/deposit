
from PySide2 import (QtWidgets, QtCore, QtGui)

class ExternalHeader(QtWidgets.QTableWidget):
	
	def __init__(self, parent, es, sheet = "0"):
		
		self.parent = parent
		self.es = es  # ExternalSource()
		self.sheet = sheet
		
		QtWidgets.QTableView.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
		self.verticalHeader().setVisible(False)
		
		columns_n = self.es.column_count(self.sheet)
		self.setRowCount(1)
		self.setColumnCount(columns_n)
		for idx in range(columns_n):
			name = self.es.column_name(self.sheet, idx)
			# set column label
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, name)
			self.setHorizontalHeaderItem(idx, item)
			
			# set target
			item = QtWidgets.QTableWidgetItem()
			item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
			item.setData(QtCore.Qt.DisplayRole, name)
			self.setItem(0, idx, item)
		
		self.adjustSize()
		
		