from deposit.DLabel import (DString, DResource, DGeometry, DNone, try_numeric)
from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.PrototypeTable import PrototypeTable
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtWidgets, QtCore, QtGui)
import numpy as np

class QueryLstView(PrototypeList, PrototypeTable, QtWidgets.QTableWidget):
	
	def __init__(self, parent_view):
		
		self._populated = False
		self._loaded_objects = []
		self._loaded_classes = []
		
		super(QueryLstView, self).__init__(parent_view)
		
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.setSortingEnabled(True)
		self.verticalHeader().hide()
		header = self.horizontalHeader().setSortIndicator(0, QtCore.Qt.AscendingOrder)
		
		self.itemSelectionChanged.connect(self.on_selection_changed)
		self.itemActivated.connect(self.on_activated)
		self.itemChanged.connect(self.on_changed)
		
		self.set_drag_and_drop_enabled()
		
		self._obj_icon = QtGui.QIcon(":res/res/object.svg")
	
	def _populate_headers(self):
		
		for column, data in enumerate(self._model.column_headers()):
			cls_id, label = self._model.column_headers()[column]
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, label)
			item.setData(QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = dict(cls_id = cls_id, column = column, value = label)))
			self.setHorizontalHeaderItem(column + 1, item)
		item = QtWidgets.QTableWidgetItem()
		item.setData(QtCore.Qt.DisplayRole, ".obj_id")
		item.setData(QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = dict(column = 0, value = ".obj_id")))
		self.setHorizontalHeaderItem(0, item)
	
	def _populate(self, update = False):
		
		if self._model.has_store() and (not self._populated) or update:
			
			self.blockSignals(True)
			
			header = self.horizontalHeader()
			sort_section = header.sortIndicatorSection()
			sort_order = header.sortIndicatorOrder()
			header.setSortIndicator(0, QtCore.Qt.AscendingOrder)
			
			if not update:
				self.clear()
				self._loaded_objects = []
				self._loaded_classes = []
			
			rows = self._model.row_count()
			columns = self._model.column_count()
			
			if not update:
				self.setRowCount(rows)
				self.setColumnCount(columns + 1) # first column is for object icon
				
				self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
				for column in range(columns):
					self.horizontalHeader().setSectionResizeMode(column + 1, QtWidgets.QHeaderView.ResizeToContents)
			
				self._populate_headers()
			
			images = [] # [data, ...]; data produced by QueryModel.table_data
			for row in range(self.rowCount()):
				for column in range(self.columnCount()):
					if not self.item(row, column):
						data = self._set_item(row, column)
						if (("image" in data["data"]) and data["data"]["image"]) or (("coords" in data["data"]) and len(data["data"]["coords"]) > 2):
							if update:
								self._model._images.append(data)
							else:
								images.append(data)
						if (column == 0) and ("obj_id" in data["data"]) and (not data["data"]["obj_id"] in self._loaded_objects):
							self._loaded_objects.append(data["data"]["obj_id"])
			self._loaded_classes = self._model.classes()
			
			if self._model.images() != images:
				self._model.set_images(images)
			
			header.setSortIndicator(sort_section, sort_order)
			
			self._populated = True
		
			self.blockSignals(False)
	
	def _set_item(self, row, column):
		
		if column == 0:
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DecorationRole, self._obj_icon)
			item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsSelectable)
			data = self._model.object_data(row)
			if "obj_id" in data["data"]:
				item.setData(QtCore.Qt.DisplayRole, try_numeric(data["data"]["value"]))
				item.setData(QtCore.Qt.UserRole, data)
		else:
			item, data = self._get_table_item(row, column - 1)
		self.setItem(row, column, item)
		return data
	
	def re_populate(self):
		
		self._populated = False
		self._populate()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if ("rel_id" in src_data) and ("rel_id" in tgt_data) and (src_data["rel_id"] == tgt_data["rel_id"]):
			return None
		if "cls_id" in tgt_data:
			if not self._model.has_relation(): # Descriptor (not displayed as relation)
				if ("cls_id" in src_data) and (src_parent in ["QueryLstView", "QueryImgView", "QueryObjView"]):
					return DropActions.ADD_DESCRIPTOR
				if src_parent == "external":
					return DropActions.ADD_RESOURCE
				if src_parent == "ExternalLstView":
					return DropActions.ADD_DESCRIPTOR
			return None
		if "obj_id" in tgt_data: # Object
			if src_parent == "external":
				return DropActions.ADD_RESOURCE
			if src_parent in ["ClassList", "QueryObjView", "ExternalLstView", "ClassLabel", "MdiClass"]:
				return DropActions.ADD_DESCRIPTOR
			if src_parent == "QueryLstView":
				if "cls_id" in src_data:
					return DropActions.ADD_DESCRIPTOR
				return DropActions.ADD_RELATION
			if src_parent in ["QueryImgView", "ObjectLabel", "MdiObject"]:
				return DropActions.ADD_RELATION
			return None
		if "parent_class" in tgt_data: # QueryLst - empty (+ parent_class) / relation - empty
			if (src_parent == "QueryLstView") and (not "cls_id" in src_data):
				if self._model.has_relation():
					return DropActions.SET_CLASS_MEMBER_ADD_RELATION
				return DropActions.SET_CLASS_MEMBER
			if src_parent in ["QueryImgView", "ObjectLabel", "MdiObject"]:
				if self._model.has_relation():
					return DropActions.SET_CLASS_MEMBER_ADD_RELATION
				return DropActions.SET_CLASS_MEMBER
		return None
	
	def selected(self):
		
		ret = [item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]
		return [data for data in ret if not data is None]
	
	def objects(self):
		
		return self._model.objects()
	
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
		grid = [[DString(self.horizontalHeaderItem(column).data(QtCore.Qt.UserRole)["data"]["value"]) for column in range(column_min, column_max + 1)]]
		self.blockSignals(True)
		for row in range(row_min, row_max + 1):
			grid_row = []
			for column in range(column_min, column_max + 1):
				if selected and (not [row, column] in indexes):
					grid_row.append(DNone())
					continue
				item = self.item(row, column)
				data = item.data(QtCore.Qt.UserRole)
				if data:
					data = data["data"]
					if ("storage_type" in data) and data["storage_type"]:
						grid_row.append(DResource(data["value"], relation = data["obj_id"]))
						continue
					if ("geometry" in data) and data["geometry"]:
						grid_row.append(DGeometry(data["value"], srid = data["srid"], relation = data["obj_id"]))
						continue
					if data["value"] is None:
						grid_row.append(DNone(relation = data["obj_id"]))
						continue
					grid_row.append(DString(data["value"], relation = data["obj_id"]))
					continue
				grid_row.append(DNone())
			grid.append(grid_row)
		self.blockSignals(False)
		return grid
	
	def paste(self, text):
		
		if self._model.has_relation():
			return
		row_min, row_max = self.rowCount() - 1, 0
		column_min, column_max = self.columnCount() - 1, 0
		for idx in self.selectedIndexes():
			row_min = min(row_min, idx.row())
			row_max = max(row_max, idx.row())
			column_min = min(column_min, idx.column())
			column_max = max(column_max, idx.column())
		column_min = max(column_min, 1)
		if column_min > column_max:
			return
		collect = []
		cls_lookup = {} # {column: cls_id, ...}
		for row, row_values in enumerate(text.split("\n")):
			row += row_min
			for column, value in enumerate(row_values.split("\t")):
				column += column_min
				item = self.item(row, column)
				if item:
					data = item.data(QtCore.Qt.UserRole)
					if data and ("cls_id" in data["data"]):
						if not column in cls_lookup:
							cls_lookup[column] = data["data"]["cls_id"]
						collect.append([row, data["data"]["cls_id"], data["data"]["obj_id"], value])
						continue
				if column in cls_lookup:
					collect.append([row, cls_lookup[column], None, value])
		if collect:
			self._model.update_data(collect)
	
	def on_store_changed(self, ids):
		
		'''
		1. if cls in deleted or ordered - re-populate
		2. re-load cells if their obj/cls pairs are in ids[updated]
		3. if obj in deleted - remove row
		4. if any obj in created and cls in updated and the same obj in updated - add row
		'''
		
		# if class in deleted or ordered - re-populate
		if self._loaded_classes and (ids["deleted"] + ids["ordered"]) and np.intersect1d(self._loaded_classes, (ids["deleted"] + ids["ordered"])).size:
			self.re_populate()
			return
		
		if self._loaded_objects and np.intersect1d(self._loaded_objects, ids["updated"]).size and [id for id in (ids["created"] + ids["updated"]) if self._model._parent_model.store.get_dep_class_by_id(id) == "Relation"]:
			self.re_populate()
			return
		
		# if loaded obj in deleted - remove row
		if self._loaded_objects and ids["deleted"]:
			to_delete = np.intersect1d(self._loaded_objects, ids["deleted"]).tolist()
			if to_delete:
				rows = []
				for row in range(self.rowCount()):
					item = self.item(row, 0).data(QtCore.Qt.UserRole)
					if item:
						if item["data"]["obj_id"] in to_delete:
							rows.append(row)
				rows = sorted(rows)[::-1]
				for row in rows:
					self.removeRow(row)
				# update row numbers for affected items
				if rows:
					for row in range(rows[-1], self.rowCount()):
						for column in range(self.columnCount()):
							item = self.item(row, column)
							if item:
								data = item.data(QtCore.Qt.UserRole)
								data["data"]["row"] = row
								item.setData(QtCore.Qt.UserRole, data)
			return
		
		# if loaded obj/cls pairs in ids[updated] - re-load affected cells
		if self._loaded_objects and self._loaded_classes and np.intersect1d(self._loaded_objects + self._loaded_classes, ids["updated"]).size:
			
			affected = self._model.get_affected_cells(ids["updated"])
			for row, column in affected:
				item = self.takeItem(row, column + 1)
				if item:
					data = item.data(QtCore.Qt.UserRole)
					try:
						i = self._model._images.index(data)
					except:
						i = -1
					if i > -1:
						del self._model._images[i]
					item = None
			self._populate(update = True)
			return
		
		# if any obj in created and cls in updated and the same obj in updated - add row
		row_diff = self._model.row_count() - self.rowCount()
		if row_diff:
			for row in range(row_diff):
				self.insertRow(self.rowCount())
			self._populate(update = True)
			print("E") # DEBUG
			return
	
	def on_activated(self, item):
		
		self._parent_view.on_activated(item)
	
	def on_changed(self, item):
		
		data = item.data(QtCore.Qt.UserRole)
		if data:
			self.blockSignals(True)
			self._model.set_data(item.data(QtCore.Qt.UserRole), item.data(QtCore.Qt.DisplayRole))
			self.blockSignals(False)
	
	def on_filter(self, text):
		
		keep = []
		for item in self.findItems(text, QtCore.Qt.MatchContains):
			if item and (not item.row() in keep):
				keep.append(item.row())
		for row in range(self.rowCount()):
			if (row in keep):
				self.showRow(row)
			else:
				self.hideRow(row)
		self._parent_view.on_count_changed(len(keep))
	
