from deposit.DLabel import (DString, DResource, DGeometry, DNone)
from deposit.commander.PrototypeList import PrototypeList
from PyQt5 import (QtWidgets, QtCore, QtGui)

class ExternalLstView(PrototypeList, QtWidgets.QTableWidget):
	
	def __init__(self, parent_view):
		
		super(ExternalLstView, self).__init__(parent_view)
		
		self.setDragEnabled(True)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
		
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().setVisible(False)
		self.verticalHeader().setVisible(False)
		
		self.itemSelectionChanged.connect(self.on_selection_changed)
		
	def _populate(self):
		
		self.setRowCount(self._model.row_count())
		self.setColumnCount(self._model.column_count())
		for row in range(self._model.row_count()):
			for column in range(self._model.column_count()):
				data = self._model.table_data(row, column)
				
				item = QtWidgets.QTableWidgetItem()
				item.setData(QtCore.Qt.UserRole, data)
				if "coords" in data["data"]:
					item.setData(QtCore.Qt.DisplayRole, data["data"]["value"].split("(")[0].strip())
					item.setData(QtCore.Qt.DecorationRole, QtGui.QIcon(":res/res/geometry.svg"))
				else:
					item.setData(QtCore.Qt.DisplayRole, data["data"]["value"])
				item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable)
				self.setItem(row, column, item)
		
		self.adjustSize()
	
	def selected(self):
		
		return [item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]
	
	def grid_data(self, selected = False):
		
		row_min = 0
		row_max = self.rowCount() - 1
		column_min = 0
		column_max = self.columnCount() - 1
		if selected:
			indexes = []
			row_min, row_max = row_max, row_min
			column_min, column_max = column_max, column_min
			for idx in self.selectedIndexes():
				indexes.append([idx.row(), idx.column()])
				row_min = min(row_min, idx.row())
				row_max = max(row_max, idx.row())
				column_min = min(column_min, idx.column())
				column_max = max(column_max, idx.column())
		grid = []
		self.blockSignals(True)
		for row in range(row_min, row_max + 1):
			grid_row = []
			for column in range(column_min, column_max + 1):
				if selected and (not [row, column] in indexes):
					grid_row.append(DNone())
					continue
				item = self.item(row, column)
				if hasattr(item, "load"):
					item.load()
				data = item.data(QtCore.Qt.UserRole)["data"]
				relation = [data["field"], data["target"], data["merge"]]
				if ("storage_type" in data) and data["storage_type"]:
					grid_row.append(DResource(data["value"], relation = relation))
					continue
				if ("geometry" in data) and data["geometry"]:
					grid_row.append(DGeometry(data["value"], srid = data["srid"], relation = relation))
					continue
				if data["value"] is None:
					grid_row.append(DNone(relation = relation))
					continue
				grid_row.append(DString(data["value"], relation = relation))
				continue
			grid.append(grid_row)
		self.blockSignals(False)
		return grid
	
	def on_set_model(self):
		
		self._populate()
	
	def on_target_changed(self, column, value, checked):
		
		for row in range(self._model.row_count()):
			item = self.item(row, column)
			data = item.data(QtCore.Qt.UserRole)
			data["data"]["target"] = value
			data["data"]["merge"] = checked
			item.setData(QtCore.Qt.UserRole, data)
