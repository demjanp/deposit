from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryItem import (QueryItem)
from deposit.commander.frames.QueryMembers.QuerySelection import (QuerySelection)
from deposit.commander.frames.QueryMembers.PrototypeDrag import (PrototypeDragView, PrototypeDragModel)

from PySide2 import (QtWidgets, QtCore, QtGui)
from natsort import (natsorted)

class ProxyModel(QtCore.QSortFilterProxyModel):
	
	def __init__(self, table_view):
		
		self.table_view = table_view
		
		super(ProxyModel, self).__init__()
	
	def lessThan(self, source_left, source_right):
		
		values = [("" if val is None else val) for val in [source_left.data(QtCore.Qt.DisplayRole), source_right.data(QtCore.Qt.DisplayRole)]]
		
		return values == natsorted(values)
	
	def sort(self, *args):
		
		QtCore.QSortFilterProxyModel.sort(self, *args)
		
		self.table_view.on_sorted()

class TableModel(DModule, PrototypeDragModel, QtCore.QAbstractTableModel):
	
	def __init__(self, model, view, query, relation, table_view):
		
		self.model = model
		self.view = view
		self.query = query
		self.relation = relation
		self.table_view = table_view
		self.class_name = None
		
		self.proxy_model = None

		DModule.__init__(self)
		QtCore.QAbstractTableModel.__init__(self)
		
		self.icons = dict(
			obj = self.view.get_icon("object.svg"),
			geo = self.view.get_icon("geometry.svg"),
			file = self.view.get_icon("file.svg"),
			image = self.view.get_icon("image.svg"),
			georaster = self.view.get_icon("georaster.svg"),
			remote_file = self.view.get_icon("remote_file.svg"),
			remote_image = self.view.get_icon("remote_image.svg"),
			remote_georaster = self.view.get_icon("remote_georaster.svg"),
		)
		
		if self.query.classes:
			self.class_name = self.query.classes[0]
		
		self.proxy_model = ProxyModel(table_view)
		self.proxy_model.setSourceModel(self)
	
	def get_query_item(self, index):
		
		if not index.isValid():
			return QueryItem(index, None, self.icons)
		row, col = index.row(), index.column()
		if col == 0:
			return QueryItem(index, self.query[row].object, self.icons, self.relation)
		name = self.query.columns[col - 1]
		if name in self.query[row]:
			item = self.query[row][name]
			if item.descriptor is None:
				return QueryItem(index, item.object, self.icons)
			else:
				return QueryItem(index, item.descriptor, self.icons)
		descr = name.split(".")
		if len(descr) == 2:
			descr = descr[1]
			if descr in self.model.descriptor_names:
				return QueryItem(index, self.model.null_descriptor(self.query[row].object, self.model.classes[descr]), self.icons)
		return QueryItem(index, None, self.icons)
	
	def rowCount(self, parent):
		
		return len(self.query)
	
	def columnCount(self, parent):

		return len(self.query.columns) + 1
	
	def flags(self, index):
		
		item = self.get_query_item(index)
		
		return PrototypeDragModel.flags(self, item)
	
	def headerData(self, section, orientation, role):
		
		if orientation == QtCore.Qt.Horizontal: # column headers
			if role == QtCore.Qt.DisplayRole:
				if section == 0:
					if self.class_name is None:
						return "id()"
					return "id(%s)" % (self.class_name)
				return self.query.columns[section - 1]
		return None
	
	def data(self, index, role):
		
		if not index.isValid():
			return None
		
		if (index.column() == 0) and (role == QtCore.Qt.DecorationRole):
			return self.icons["obj"]
		
		item = self.get_query_item(index)
		
		return item.data(role)
	
	def setData(self, index, value, role = QtCore.Qt.EditRole):
		
		if role == QtCore.Qt.EditRole:
			item = self.get_query_item(index)
			obj = item.element.target
			cls = item.element.dclass
			self.table_view.parent.set_edited(True)
			obj.descriptors.add(cls, value)
			
			self.query.update()
			
			QtCore.QAbstractTableModel.setData(self, index, value, role)
		
		return False
	
	def drag_supported(self, item):
		
		return True # DEBUG
	
	def drop_supported(self, item):
		
		return True # DEBUG
	
	def on_drop_url(self, item, urls):
		
		obj = item.element.target
		cls = item.element.dclass
		obj.descriptors.add(cls, urls[0], "DResource")
	
	def on_drop_text(self, item, text):
		
		obj = item.element.target
		cls = item.element.dclass
		obj.descriptors.add(cls, text)
	
	def on_drop_elements(self, item, elements):
		
		element = elements[0]
		if element.__class__.__name__ == "DDescriptor":
			obj = item.element.target
			cls = item.element.dclass
			obj.descriptors.add(cls, element.label)

class QueryLst(Frame, PrototypeDragView, QtWidgets.QTableView):
	
	def __init__(self, model, view, parent, query, relation = None):
		
		self.query = query
		self.table_model = None
		self.relation = relation
		self._selection = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QTableView.__init__(self, parent)
		
		self.set_up()
		self.set_up_drag_drop()
	
	def set_up(self):
		
		self.table_model = TableModel(self.model, self.view, self.query, self.relation, self)
		
		self.setSortingEnabled(True)
		self.horizontalHeader().setSortIndicator(0, QtCore.Qt.AscendingOrder)
		self.setStyleSheet('''
			QTableView::item:selected:!active {
				background-color : #81b0d6;
			}
		''')
		self.setIconSize(QtCore.QSize(24, 24))
		
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		
		self.setModel(self.table_model.proxy_model)
		
		try: self.activated.disconnect()
		except: pass
		self.activated.connect(self.on_activated)

		self._selection = QuerySelection(self.model, self.view, self.selectionModel().selectedIndexes())
		header = self.horizontalHeader()
		for i in range(header.count()):
			header.resizeSection(i, header.sectionSizeHint(i))
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def filter(self, text):
		
		if text == "":
			self.table_model.proxy_model.setFilterWildcard("")
		else:
			self.table_model.proxy_model.setFilterRegExp(QtCore.QRegExp(".*%s.*" % text, QtCore.Qt.CaseInsensitive))
		self.table_model.proxy_model.setFilterKeyColumn(-1)
	
	def clear_selection(self):
	
		self.clearSelection()
	
	def select_next_row(self):
		
		rows = self.table_model.rowCount(None)
		if rows:
			row = -1
			for index in self.selectionModel().selectedIndexes():
				row = index.row() if (row == -1) else min(row, index.row())
			if row < rows - 1:
				self.selectRow(row + 1)
			else:
				self.selectRow(0)
	
	def select_previous_row(self):
		
		rows = self.table_model.rowCount(None)
		if rows:
			row = -1
			for index in self.selectionModel().selectedIndexes():
				row = index.row() if (row == -1) else min(row, index.row())
			if row > 0:
				self.selectRow(row - 1)
			else:
				self.selectRow(rows - 1)
	
	def select_last_row(self):

		rows = self.table_model.rowCount(None)
		if rows:
			self.selectRow(rows - 1)
	
	def select_object(self, obj):

		if obj.__class__.__name__ != "DObject":
			obj = self.model.objects[obj]
		for row in range(self.table_model.proxy_model.rowCount()):
			if self.get_row_object(row) == obj:
				self.selectRow(row)
				return
		self.selectRow(0)
	
	def get_query_item(self, row, column):
		
		return self.table_model.proxy_model.data(self.table_model.proxy_model.index(row, column), QtCore.Qt.UserRole)
	
	def set_query_item(self, row, column, value):
		
		self.table_model.proxy_model.setData(self.table_model.proxy_model.index(row, column), value)
	
	def get_mime_data(self, indexes):
		
		return self.table_model.mimeData(indexes)
	
	def process_drop(self, item, data):
		
		self.table_model.process_drop(item, data)
	
	def get_row_object(self, row):
		
		return self.table_model.proxy_model.data(self.table_model.proxy_model.index(row, 0), QtCore.Qt.UserRole).element
	
	def get_row_ids(self):
		# returns {object id: row, ...}
		
		return dict([(self.get_row_object(row).id, row) for row in range(self.get_row_count())])
	
	def get_selected(self):
		# return [[QueryItem, ...], ...]; for every column & row in selected range
		# return QuerySelection instance

		return self._selection
	
	def get_objects(self):
		
		return [self.get_row_object(row) for row in range(self.get_row_count())]
	
	def get_first_selected(self):
		# return [DObject, row number]

		rows = self.get_selected().rows()
		if rows:
			return [self.get_row_object(rows[0]), rows[0]]
		return [None, None]

	def get_selected_objects(self):
		# return {row: DObject, ...}

		return dict([(row, self.get_row_object(row)) for row in self.get_selected().rows()])
	
	def get_row_count(self):
		
		return self.table_model.proxy_model.rowCount()
	
	def get_column_count(self):
		
		return self.table_model.proxy_model.columnCount()
	
	def sizeHint(self):
		
		w = self.columnWidth(0) + self.columnWidth(1) * (self.table_model.columnCount(None) - 1) * 1.05
		w = max(w, 200)
		h = self.rowHeight(0) * (self.table_model.rowCount(None) + 1) * 1.05
		return QtCore.QSize(w, h)
	
	@QtCore.Slot(QtCore.QModelIndex)
	def on_activated(self, index):
		
		item = index.data(QtCore.Qt.UserRole)
		if item.element.__class__.__name__ == "DObject":
			if self.relation:
				cls = item.element.first_class()
				self.parent.on_query_activated("SELECT %s.* WHERE id(%s) == %d" % (cls, cls, item.element.id))
				return
			self.parent.on_object_activated(item.element)
			return
		if item.element.__class__.__name__ == "DDescriptor":
			self.parent.on_descriptor_activated(item.element)
			return
	
	def on_sorted(self):
		
		self.parent.on_sorted()
	
	def selectionChanged(self, selected, deselected):

		super(QueryLst, self).selectionChanged(selected, deselected)
		self._selection = QuerySelection(self.model, self.view, self.selectionModel().selectedIndexes())
		self.broadcast(Broadcasts.VIEW_SELECTED)
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def focusInEvent(self, event):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
		super(QueryLst, self).focusInEvent(event)
	
	def focusOutEvent(self, event):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
		super(QueryLst, self).focusOutEvent(event)

