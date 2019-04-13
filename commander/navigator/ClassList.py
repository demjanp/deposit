from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtCore, QtWidgets, QtGui)

class ClassList(Frame, QtWidgets.QTreeWidget):
	
	def __init__(self, model, view, parent):
		
		self.class_names = []
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QTreeWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.setHeaderHidden(True)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.setExpandsOnDoubleClick(False)
		self.setIconSize(QtCore.QSize(24,24))
		self.setColumnCount(1)
		
		self.connect_broadcast(Broadcasts.ELEMENT_ADDED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_DELETED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		
		self.itemActivated.connect(self.on_activated)
		self.itemSelectionChanged.connect(self.on_selected)
		
		self.populate()
	
	def populate(self):
		
		selected = self.get_selected()
		
		self.clear()
		
		icon_obj = self.view.get_icon("object.svg")
		icon_cls = self.view.get_icon("class.svg")
		icon_descr = self.view.get_icon("descriptor.svg")
		
		self.class_names = ["[classless objects]"] + [name for name in self.model.classes if not name in self.model.descriptor_names]
		items = []
		for cls in self.class_names:
			item = QtWidgets.QTreeWidgetItem()
			item.descriptor = False
			item.setData(0, QtCore.Qt.DisplayRole, cls)
			if cls == "[classless objects]":
				item.setData(0, QtCore.Qt.UserRole, "!*")
				item.setData(0, QtCore.Qt.DecorationRole, icon_obj)
			else:
				item.setData(0, QtCore.Qt.UserRole, cls)
				item.setData(0, QtCore.Qt.DecorationRole, icon_cls)
			subitems = []
			for descr in self.model.classes[cls].descriptors:
				subitem = QtWidgets.QTreeWidgetItem()
				subitem.descriptor = True
				subitem.setData(0, QtCore.Qt.DisplayRole, descr)
				subitem.setData(0, QtCore.Qt.UserRole, descr)
				subitem.setData(0, QtCore.Qt.DecorationRole, icon_descr)
				subitems.append(subitem)
			if subitems:
				item.insertChildren(0, subitems)
			items.append(item)
		if items:
			self.insertTopLevelItems(0, items)
		self.expandAll()
		
		if selected:
			self.set_selected(selected)
	
	def get_selected(self):
		
		return [item.data(0, QtCore.Qt.UserRole) for item in self.selectedItems()]
		
	def get_selected_parent(self):
		
		parent = self.selectedItems()[0].parent()
		if parent is None:
			return None
		return parent.data(0, QtCore.Qt.UserRole)
	
	def set_selected(self, names):
		
		iterator = QtWidgets.QTreeWidgetItemIterator(self)
		while iterator.value():
			item = iterator.value()
			name = item.data(0, QtCore.Qt.UserRole)
			if name in names:
				item.setSelected(True)
				names.remove(name) # select only the first occurence of name
			iterator += 1
	
	def on_selected(self):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_activated(self, item, column):

		name = item.data(0, QtCore.Qt.UserRole)

		if name == "!*":
			self.view.mdiarea.create("Query", "SELECT !*.*")
		elif name in self.class_names:
			if ("." in name) or (" " in name):
				name = "\"%s\"" % name
			self.view.mdiarea.create("Query", "SELECT %s.*" % (name))
		else:
			self.view.mdiarea.create("Query", "SELECT *.%s" % (name))
	
	def on_loaded(self, args):
		
		self.populate()
	
	def on_store_changed(self, args):

		for _, elements in args:
			if isinstance(elements, list):
				for element in elements:
					if element.__class__.__name__ == "DClass":
						self.populate()
						return
			else:
				if elements.__class__.__name__ == "DClass":
					self.populate()

	def mousePressEvent(self, event):

		pass # TODO deactivate MDIArea windows

		QtWidgets.QTreeWidget.mousePressEvent(self, event)
