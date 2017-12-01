from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.PrototypeTable import PrototypeTable
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtWidgets, QtCore)
import numpy as np

class QueryObjView(PrototypeList, PrototypeTable, QtWidgets.QTableWidget):
	
	def __init__(self, parent_view):
		
		self._obj_id = None
		self._row = None
		self._obj_data = None
		self._populated = False
		self._loaded_classes = []
		
		super(QueryObjView, self).__init__(parent_view)
		
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().hide()
		
		self.itemSelectionChanged.connect(self.on_selection_changed)
		self.itemActivated.connect(self.on_activated)
		self.itemChanged.connect(self.on_changed)
		
		self.set_drag_and_drop_enabled()
	
	def _populate(self):
		
		self.blockSignals(True)
		
		if self._model.has_store() and not self._populated:
			
			self.clear()
			
			self._loaded_classes = []
			columns = self._model.column_count()
			self.setRowCount(columns)
			self.setColumnCount(1)
			self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
			
			# set row labels
			for col, data in enumerate(self._model.column_headers()):
				cls_id, label = data
				item = QtWidgets.QTableWidgetItem()
				item.setData(QtCore.Qt.DisplayRole, label)
				item.setData(QtCore.Qt.UserRole, dict(cls_id = cls_id, column = col))
				self.setVerticalHeaderItem(col, item)
				for cls_id in cls_id.split("."):
					if not cls_id in self._loaded_classes:
						self._loaded_classes.append(cls_id)
			
			self._populated = True
			
		self.blockSignals(False)
	
	def re_populate(self):
		
		self._populated = False
		self._populate()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "external":
			return DropActions.ADD_RESOURCE
		if "cls_id" in tgt_data: # Descriptor
			if "cls_id" in src_data:
				return DropActions.ADD_DESCRIPTOR
			if src_parent == "ExternalLstView":
				return DropActions.ADD_DESCRIPTOR
			return None
		# empty:
		if src_parent in ["ClassList", "QueryObjView", "ExternalLstView", "ClassLabel", "MdiClass"]:
			return DropActions.ADD_DESCRIPTOR
		if src_parent == "QueryLstView":
			if "cls_id" in src_data:
				return DropActions.ADD_DESCRIPTOR
			return DropActions.ADD_RELATION
		if src_parent in ["QueryImgView", "ObjectLabel", "MdiObject"]:
			return DropActions.ADD_RELATION
		return None
	
	def set_row(self, row):
		
		if row >= len(self._model.objects()):
			return
		self._obj_id = self._model.objects()[row]
		self._row = row
		
		self.blockSignals(True)
		for column in range(self._model.column_count()):
			
			self.setItem(column, 0, self._get_table_item(self._row, column)[0])
		
		self.blockSignals(False)
	
	def row(self):
		
		return self._row
	
	def obj_id(self):
		
		return self._obj_id
	
	def selected(self):
		
		return [item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]
	
	def on_set_model(self):
		
		self._populate()
	
	def on_store_changed(self, ids):
		
		if not self._model.has_store():
			return
		if (self._obj_id and np.intersect1d(self._loaded_classes + [self._obj_id], ids["created"] + ids["updated"] + ids["deleted"] + ids["ordered"]).size) or (not self._loaded_classes):
			self.re_populate()
			if not self._row is None:
				self.set_row(self._row)
	
	def on_activated(self, item):
		
		self._parent_view.on_activated(item)
	
	def on_changed(self, item):
		
		self.blockSignals(True)
		self._model.set_data(item.data(QtCore.Qt.UserRole), item.data(QtCore.Qt.DisplayRole))
		self.blockSignals(False)

