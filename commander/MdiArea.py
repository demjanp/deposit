from deposit.commander.PrototypeFrame import PrototypeFrame
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtWidgets, QtCore, QtGui)
import json
import os
from urllib.parse import urlparse

class MdiDrag(QtWidgets.QMdiSubWindow):
	
	def __init__(self, parent_view, icon, tooltip):
		
		self._parent_view = parent_view
		
		super(MdiDrag, self).__init__()
		
		self.label = QtWidgets.QLabel()
		self.label.setPixmap(QtGui.QPixmap(icon))
		self.label.setToolTip(tooltip)
		self.label.setCursor(QtCore.Qt.OpenHandCursor)
		self.setWidget(self.label)
		self.setStyleSheet("background-color:transparent;")
	
	def mousePressEvent(self, event):
		
		mimeData = QtCore.QMimeData()
		mimeData.setData("application/deposit", bytes(json.dumps(dict(parent = self.__class__.__name__, data = [{}])), "utf-8"))
		
		drag = QtGui.QDrag(self)
		drag.setMimeData(mimeData)
		drag.setPixmap(self.label.pixmap())
		drag.setHotSpot(event.pos() - self.label.pos())
		dropAction = drag.exec(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
	
	def eventFilter(self, watched, event):
		if event.type() == QtCore.QEvent.Enter:
			self._parent_view.on_action_hovered(self.label)
		return super(MdiDrag, self).eventFilter(watched, event)

class MdiObject(MdiDrag):
	
	pass

class MdiClass(MdiDrag):
	
	pass

class MdiTrash(PrototypeFrame, QtWidgets.QMdiSubWindow):
	
	def __init__(self, parent_view):
		
		super(MdiTrash, self).__init__(parent_view)
		
		self.setAcceptDrops(True)
		
		self.label = QtWidgets.QLabel()
		self.label.setPixmap(QtGui.QPixmap(":/res/res/trash_closed.svg"))
		self.label.setToolTip("Drop items here to delete")
		self.setWidget(self.label)
		self.setStyleSheet("background-color:transparent;")
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "ClassList":
			if "parent_class" in src_data:
				if not "#" in src_data["parent_class"]:
					return DropActions.DELETE_CLASS_MEMBER
			return DropActions.DELETE_CLASS
		if src_parent == "ClassLabel":
			if not "#" in src_data["cls_id"]:
				return DropActions.DELETE_CLASS_MEMBER
		if src_parent == "ObjectLabel":
			if not "#" in src_data["obj_id"]:
				return DropActions.DELETE_OBJECT
		if src_parent == "QueryLstView":
			if "obj_id2" in src_data:
				if not "cls_id" in src_data:
					return DropActions.DELETE_RELATION
				return None
			if "cls_id" in src_data:
				if not "#" in src_data["cls_id"]:
					return DropActions.DELETE_DESCRIPTOR
			if not "#" in src_data["obj_id"]:
				return DropActions.DELETE_OBJECT
		if src_parent in ["QueryImgView", "QueryObjView"]:
			if not "#" in src_data["rel_id"]:
				return DropActions.DELETE_DESCRIPTOR
		return None
	
	def on_drag_move(self, source, target, event):
		
		self.label.setPixmap(QtGui.QPixmap(":/res/res/trash_open.svg"))
	
	def on_drag_leave(self, event):
		
		self.label.setPixmap(QtGui.QPixmap(":/res/res/trash_closed.svg"))
	
	def on_drop(self, event):
		
		self.label.setPixmap(QtGui.QPixmap(":/res/res/trash_closed.svg"))
	
	def eventFilter(self, watched, event):
		if event.type() == QtCore.QEvent.Enter:
			self._parent_view.on_action_hovered(self.label)
		return super(MdiTrash, self).eventFilter(watched, event)
	
class MdiSubWindow(QtWidgets.QMdiSubWindow):
	
	def __init__(self, *args, **kwargs):
		
		super(MdiSubWindow, self).__init__(*args, **kwargs)
		
		self.windowStateChanged.connect(self.on_state_changed)
	
	def on_state_changed(self, old_state, new_state):
		
		if new_state == QtCore.Qt.WindowActive:
			widget = self.widget()
			found = []
			for key in widget.__dict__:
				child = widget.__dict__[key]
				if (isinstance(child, QtWidgets.QAbstractItemView) or isinstance(child, QtWidgets.QGraphicsView)) and child.isVisible():
					found.append(child)
					if child.selected():
						child.setFocus()
						return
			if found:
				found[0].setFocus()
			if (isinstance(widget, QtWidgets.QAbstractItemView) or isinstance(widget, QtWidgets.QGraphicsView)):
				widget.setFocus()
				return
		
class MdiArea(PrototypeFrame, QtWidgets.QMdiArea):
	
	def __init__(self, parent_view):
		
		super(MdiArea, self).__init__(parent_view)
		
		self.setAcceptDrops(True)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self._populate()
		self.verticalScrollBar().valueChanged.connect(self.on_scroll)
		self.horizontalScrollBar().valueChanged.connect(self.on_scroll)
	
	def _populate(self):
		
		self.objectDrag = MdiObject(self._parent_view, ":/res/res/object.svg", "Drag & Drop to create new Object")
		self.objectDrag.setGeometry(10, 10, 32, 32)
		self.addSubWindow(self.objectDrag, QtCore.Qt.FramelessWindowHint)
		
		self.classDrag = MdiClass(self._parent_view, ":/res/res/class.svg", "Drag & Drop to create new Class")
		self.classDrag.setGeometry(48, 10, 32, 32)
		self.addSubWindow(self.classDrag, QtCore.Qt.FramelessWindowHint)
		
		self.trash = MdiTrash(self._parent_view)
		self.trash.setGeometry(48, 10, 32, 32)
		self.addSubWindow(self.trash, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
		
		self.subWindowActivated.connect(self._parent_view.on_subwindow_activated)
		
		self.update_drags()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		# TODO use MdiAreaModel to access model functions

		if src_parent == "external":
			scheme = urlparse(src_data["value"]).scheme
			if (scheme in ["http", "https"]) or (os.path.splitext(src_data["value"])[1].lower() == ".rdf"):
				return DropActions.OPEN_DATABASE
		if not self._parent_view._model.has_store():
			return None
		if src_parent in ["QueryImgView", "QueryObjView", "ObjectLabel", "MdiObject"]:
			return DropActions.OPEN_OBJECT
		if src_parent in ["ClassList", "ClassLabel", "MdiClass"]:
			return DropActions.OPEN_CLASS
		if src_parent == "external":
			if self._parent_view._model.store.file.shapefiles.is_shapefile(src_data["value"]) or self._parent_view._model.store.file.xlsx.is_xlsx(src_data["value"]):
				return DropActions.OPEN_EXTERNAL
			return None
		if src_parent == "QueryLstView":
			if ("cls_id" in src_data) and ((("image" in src_data) and src_data["image"]) or (("geometry" in src_data) and src_data["geometry"])):
				return DropActions.OPEN_DESCRIPTOR
			return DropActions.OPEN_OBJECT
		return None
	
	def set_object_drag_enabled(self, state):
		
		self.objectDrag.setEnabled(state)
	
	def set_class_drag_enabled(self, state):
		
		self.classDrag.setEnabled(state)
	
	def set_trash_enabled(self, state):
		
		self.trash.setEnabled(state)
	
	def add_window(self, widget):
		
		sub = MdiSubWindow(flags = QtCore.Qt.SubWindow)
		sub.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		sub.setWidget(widget)
		self.addSubWindow(sub)
		pos = sub.pos()
		pos.setX(pos.x() + 100) # move from under dockWidget
		sub.move(pos)
		sub.show()
	
	def update_drags(self):
		
		self.objectDrag.move(10, 10)
		self.classDrag.move(48, 10)
		self.trash.move(self.rect().width() - 70, self.rect().height() - 70)
	
	def on_drop(self, event):
		
		if self.objectDrag.geometry().contains(event.pos()) or self.classDrag.geometry().contains(event.pos()):
			return
		if (event.source() in [self.objectDrag, self.classDrag]) and self.trash.geometry().contains(event.pos()):
			return
	
	def on_scroll(self):
		
		self.update_drags()
	
	def resizeEvent(self, event):
		
		self.update_drags()
