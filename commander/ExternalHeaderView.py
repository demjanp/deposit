from deposit.commander.PrototypeList import PrototypeList
from PyQt5 import (QtWidgets, QtCore)

class ExternalHeaderView(PrototypeList, QtWidgets.QTableWidget):
	
	target_changed = QtCore.pyqtSignal(int, str, bool) # column, value, checked
	
	def __init__(self, parent_view):
		
		super(ExternalHeaderView, self).__init__(parent_view)
		
		self.itemChanged.connect(self.on_changed)
		
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
		self.verticalHeader().setVisible(False)
		
	def _populate(self):
		
		self.setRowCount(1)
		self.setColumnCount(self._model.column_count())
		for column, label in enumerate(self._model.column_headers()):
			# set column label
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, label)
			item.setData(QtCore.Qt.UserRole, dict(value = label, column = column))
			self.setHorizontalHeaderItem(column, item)
			# set target
			label = label.strip("#")
			item = QtWidgets.QTableWidgetItem()
			item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
			item.setData(QtCore.Qt.DisplayRole, label)
			item.setData(QtCore.Qt.UserRole, dict(value = label, column = column))
			item.setData(QtCore.Qt.CheckStateRole, QtCore.Qt.Unchecked)
			self.setItem(0, column, item)
		
		self.adjustSize()
	
	def on_set_model(self):
		
		self._populate()
	
	def on_changed(self, item):
		
		self.target_changed.emit(item.data(QtCore.Qt.UserRole)["column"], item.data(QtCore.Qt.DisplayRole), (item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked))
	
