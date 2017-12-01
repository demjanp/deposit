from deposit.commander.PrototypeFrame import PrototypeFrame
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtWidgets, QtCore, QtGui)
import numpy as np
import json

class ClassLabel(QtWidgets.QWidget):
	
	def __init__(self, parent_frame, cls_id, label, obj_id):
		
		self._parent_frame = parent_frame
		self._cls_id = cls_id
		self._obj_id = obj_id
		super(ClassLabel, self).__init__()
		
		label_icon = QtWidgets.QLabel()
		label_icon.setPixmap(QtGui.QPixmap(":res/res/class.svg").scaledToHeight(24, QtCore.Qt.SmoothTransformation))
		label_text = QtWidgets.QLabel(label)
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().setSpacing(0)
		self.layout().addWidget(label_icon)
		self.layout().addWidget(label_text)
		self.setStyleSheet("QWidget {background-color : #dddddd;} QLabel {padding : 3px;}")
		self.setCursor(QtCore.Qt.OpenHandCursor)
	
	def cls_id(self):
		
		return self._cls_id
	
	def mousePressEvent(self, event):
		
		mimeData = QtCore.QMimeData()
		mimeData.setData("application/deposit", bytes(json.dumps(dict(parent = self.__class__.__name__, data = [dict(obj_id = self._obj_id, cls_id = self._cls_id)])), "utf-8"))
		
		drag = QtGui.QDrag(self)
		drag.setMimeData(mimeData)
		rect = self.rect()
		pixmap = QtGui.QPixmap(rect.size())
		self.render(pixmap, QtCore.QPoint(), QtGui.QRegion(rect))
		drag.setPixmap(pixmap)
		drag.setHotSpot(event.pos() - self.pos())
		dropAction = drag.exec(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
	
	def mouseDoubleClickEvent(self, event):
		
		self._parent_frame.on_double_click(self._cls_id)

class ClassesFrame(PrototypeFrame, QtWidgets.QFrame):
	
	def __init__(self, parent_view):
		
		self._model = None
		self._obj_id = None
		
		super(ClassesFrame, self).__init__(parent_view)

		self.setAcceptDrops(True)
		
		self.setLayout(QtWidgets.QHBoxLayout())
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().addStretch()
	
	def _populate(self):
		
		# clear layout
		layout = self.layout()
		for i in reversed(range(layout.count())):
			widget = layout.itemAt(i).widget()
			if isinstance(widget, ClassLabel) or isinstance(widget, QtWidgets.QLabel):
				widget.setParent(None)
		# add Class labels
		if self._model.has_store():
			found = False
			if not self._obj_id is None:
				for cls_id, label in self._model.object_classes(self._obj_id):
					found = True
					label_class = ClassLabel(self, cls_id, label, self._obj_id)
					self.layout().insertWidget(0, label_class)
			if not found:
				label_classless = QtWidgets.QLabel("Classless Object")
				label_classless.setStyleSheet("QWidget {background-color : #dddddd;} QLabel {padding : 3px;}")
				self.layout().insertWidget(0, label_classless)
	
	def set_model(self, model):
		
		self._model = model
	
	def set_object(self, obj_id):
		
		self._obj_id = obj_id
		self._populate()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent in ["ClassList", "ClassLabel", "MdiClass"]:
			return DropActions.SET_CLASS_MEMBER
		return None
	
	def get_data(self):
		
		return dict(
			obj_id = self._obj_id,
		)
	
	def on_store_changed(self, ids):
		
		cls_ids = []
		for i in range(self.layout().count()):
			widget = self.layout().itemAt(i).widget()
			if isinstance(widget, ClassLabel):
				cls_ids.append(widget.cls_id())
		if ids and ((self._obj_id in ids["updated"]) or (self._obj_id in ids["deleted"]) or np.in1d(cls_ids, ids["updated"]).any()):
			self._populate()
	
	def on_double_click(self, cls_id):
		
		item = QtWidgets.QTableWidgetItem(0)
		item.setData(QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = dict(obj_id = self._obj_id, cls_id = cls_id)))
		self._parent_view.on_activated(item)
	
	def on_drag_move(self, source, target, event):
		
		self.setStyleSheet("ClassesFrame {border: 1px solid black;}")
	
	def on_drag_leave(self, event):
		
		self.setStyleSheet("ClassesFrame {border: none;}")
	
	def on_drop(self, event):
		
		self.setStyleSheet("ClassesFrame {border: none;}")
