
from PyQt5 import (QtWidgets, QtCore, QtGui)

class ExternalLst(QtWidgets.QTableWidget):
	
	def __init__(self, parent, es, sheet = "0"):
		
		self.parent = parent
		self.es = es  # ExternalSource()
		self.sheet = sheet
		
		QtWidgets.QTableView.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().setVisible(False)
		self.verticalHeader().setVisible(False)
		
		rows_n = self.es.row_count(self.sheet)
		
		if not rows_n:
			return
		
		columns_n = self.es.column_count(self.sheet)
		
		self.setRowCount(rows_n)
		self.setColumnCount(columns_n)
		
		for row_idx in range(rows_n):
			for column_idx in range(columns_n):
				data = self.es.data(self.sheet, row_idx, column_idx)
				
				item = QtWidgets.QTableWidgetItem()
				item.setData(QtCore.Qt.UserRole, data)
				if data.__class__.__name__ == "DString":
					item.setData(QtCore.Qt.DisplayRole, data.value)
				elif data.__class__.__name__ == "DGeometry":
					item.setData(QtCore.Qt.DisplayRole, data.type)
					item.setData(QtCore.Qt.DecorationRole, self.parent.view.get_icon("geometry.svg"))
				item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
				
				self.setItem(row_idx, column_idx, item)
		
		self.adjustSize()
	
