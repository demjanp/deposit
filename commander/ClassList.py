from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtCore, QtWidgets, QtGui)

class ClassListItem(QtWidgets.QTreeWidgetItem):
	
	def __init__(self, model, cls_id, parent_class = None, row = None):
		
		self._model = model
		self._cls_id = cls_id
		self._row = row
		self._parent_class = parent_class
		
		super(ClassListItem, self).__init__()
		
		self._populate()
		self._model.store_changed.connect(self.on_store_changed)
	
	def _populate(self):
		
		if self._cls_id == "!*":
			self.setData(0, QtCore.Qt.DisplayRole, "Classless Objects")
		else:
			self.setData(0, QtCore.Qt.DisplayRole, self._model.store.get_label(self._cls_id).value)
		data = dict(
			cls_id = self._cls_id,
		)
		if not self._row is None:
			data["row"] = self._row
		if self._parent_class:
			data["parent_class"] = self._parent_class
		self.setData(0, QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = data))
		if self._cls_id == "!*":
			icon = QtGui.QIcon(":res/res/object.svg")
		elif self._model.store.classes.is_descriptor(self._cls_id):
			icon = QtGui.QIcon(":res/res/descriptor.svg")
		else:
			icon = QtGui.QIcon(":res/res/class.svg")
		self.setData(0, QtCore.Qt.DecorationRole, icon)
		self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsSelectable)
	
	def on_store_changed(self, ids):
		
		if not self._model.has_store():
			return
		data = self.data(0, QtCore.Qt.UserRole)
		cls_id = data["data"]["cls_id"]
		if cls_id in ids["updated"]:
			self.treeWidget().blockSignals(True)
			self._populate()
			self.treeWidget().blockSignals(False)

class ClassList(PrototypeList, QtWidgets.QTreeWidget):
	
	def __init__(self, parent_view):
		
		super(ClassList, self).__init__(parent_view)
		
		self.setHeaderHidden(True)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.setIconSize(QtCore.QSize(24,24))
		self.setColumnCount(1)
		
		self.itemActivated.connect(self.on_activated)
		self.itemSelectionChanged.connect(self.on_selection_changed)
		self.itemChanged.connect(self.on_changed)
		
		self.set_drag_and_drop_enabled()
	
	def _populate(self):
		
		self.clear()
		if self._model.has_store():
			classes = self._model.store.classes.get()
			classes = ["!*"] + sorted(classes, key = lambda cls_id: self._model.store.get_order(cls_id))
			items = []
			for row, cls_id in enumerate(classes):
				parents = self._model.store.members.get_parents(cls_id)
				item = ClassListItem(self._model, cls_id, row = row, parent_class = parents[0] if parents.size else None)
				subclasses = sorted(self._model.store.members.get_subclasses(cls_id), key = lambda subcls_id: self._model.store.get_order(subcls_id))
				subitems = [ClassListItem(self._model, subcls_id, parent_class = cls_id) for subcls_id in subclasses]
				if subitems:
					item.insertChildren(0, subitems)
				items.append(item)
			items = [item for item in items if (item._parent_class is None)]
			if items:
				self.insertTopLevelItems(0, items)
#			self.expandAll()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent in ["ClassList", "ClassLabel", "QueryLstView", "QueryImgView", "ObjectLabel", "MdiObject"]:
			if "cls_id" in tgt_data:
				return DropActions.SET_CLASS_MEMBER
			return
		if src_parent == "MdiClass":
			if "cls_id" in tgt_data:
				return DropActions.SET_CLASS_MEMBER
			return DropActions.ADD_CLASS
		return None
		
	def selected(self):
		
		return [item.data(0, QtCore.Qt.UserRole) for item in self.selectedItems()]
	
	def on_set_model(self):
		
		self._populate()
	
	def on_store_changed(self, ids):
		
		ids_all = ids["created"] + ids["updated"] + ids["deleted"] + ids["ordered"]
		if (not self._model.has_store()) or ((not ids_all) or [id for id in ids_all if (self._model.store.get_dep_class_by_id(id) == "Class")]): # reload all if no ids specified or class created
			self._populate()
	
	def on_activated(self, item, column):
		
		self._parent_view.open_class(item.data(0, QtCore.Qt.UserRole)["data"]["cls_id"])
	
	def on_actionRenameClass_clicked(self, *args):
		
		self.blockSignals(True)
		item = self.selectedItems()[0]
		default_flags = item.flags()
		item.setFlags(default_flags | QtCore.Qt.ItemIsEditable)
		self.edit(self.selectedIndexes()[0])
		item.setFlags(default_flags)
		self.blockSignals(False)
		
	def on_actionClassOrderUp_clicked(self, *args):
		
		current = self.selected()[0]["data"]
		prev = self.topLevelItem(current["row"] - 1).data(0, QtCore.Qt.UserRole)["data"]
		self._model.store.swap_order(current["cls_id"], prev["cls_id"])
		self.setCurrentItem(self.topLevelItem(prev["row"]))
		
	def on_actionClassOrderDown_clicked(self, *args):
		
		current = self.selected()[0]["data"]
		next = self.topLevelItem(current["row"] + 1).data(0, QtCore.Qt.UserRole)["data"]
		self._model.store.swap_order(current["cls_id"], next["cls_id"])
		self.setCurrentItem(self.topLevelItem(next["row"]))
		
	def on_changed(self, item):
		
		self.blockSignals(True)
		name = item.data(0, QtCore.Qt.DisplayRole)
		cls_id = item.data(0, QtCore.Qt.UserRole)["data"]["cls_id"]
		if name != "":
			self._model.actions.rename_class(cls_id, name)
		self.blockSignals(False)
