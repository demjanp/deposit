from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.PrototypeDrag import (PrototypeDragWidget)

from PySide2 import (QtWidgets, QtCore, QtGui)

class ObjView(Frame, PrototypeDragWidget, QtWidgets.QTableWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QTableWidget.__init__(self, parent)
		
		self.set_up()
		self.set_up_drag_drop()
	
	def set_up(self):
		
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.horizontalHeader().hide()
		
		self.setStyleSheet("QTableView::item:selected:!active {background-color : #81b0d6;}")
		
		self.itemSelectionChanged.connect(self.on_selection_changed)
		self.itemActivated.connect(self.on_activated)
		
		self.populate_headers()
		
	def populate_headers(self):
		
		self.blockSignals(True)
		self.setRowCount(len(self.query.columns))
		self.setColumnCount(1)
		self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		for col, column in enumerate(self.query.columns):
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, column)
			item.setData(QtCore.Qt.UserRole, column)
			self.setVerticalHeaderItem(col, item)
		self.blockSignals(False)
	
	def populate_data(self, query_lst, row):
		
		self.blockSignals(True)
		
		for col in range(self.rowCount()):
			table_item = QtWidgets.QTableWidgetItem()
			
			query_item = query_lst.get_query_item(row, col + 1)
			if query_item is None:
				continue
			
			table_item.setFlags(self.flags(query_item))
			
			for role in [QtCore.Qt.DisplayRole, QtCore.Qt.DecorationRole, QtCore.Qt.BackgroundRole, QtCore.Qt.UserRole]:
				table_item.setData(role, query_item.data(role))
			self.setItem(col, 0, table_item)
		
		self.blockSignals(False)
	
	def get_selected(self):
		
		return [[item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]]
	
	def on_query_selected(self):
		
		self.populate_data()

	def on_selection_changed(self, *args):
		
		self.broadcast(Broadcasts.VIEW_SELECTED)
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_activated(self, item):
		
		element = item.data(QtCore.Qt.UserRole).element
		if element.__class__.__name__ == "DDescriptor":
			self.broadcast(Broadcasts.VIEW_DESCRIPTOR_ACTIVATED, element)
	
	def closeEditor(self, editor, hint):
		
		QtWidgets.QTableWidget.closeEditor(self, editor, hint)
		
		item = self.currentItem()
		value = item.data(QtCore.Qt.DisplayRole)
		element = item.data(QtCore.Qt.UserRole).element
		obj = element.target
		cls = element.dclass
		obj.descriptors.add(cls, value)
		
	def drag_supported(self, item):
		
		return False # DEBUG
		
	def drop_supported(self, item):
		
		if not item.is_object():
			return True
		return False
		
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
