from deposit.commander.PrototypeFrame import PrototypeFrame
from deposit.commander.DropActions import DropActions
from deposit.DLabel import (id_to_name)
from PyQt5 import (QtWidgets, QtCore, QtGui)
import json

class ObjectLabel(QtWidgets.QWidget):
	
	def __init__(self, parent_frame, obj_id):
		
		self._parent_frame = parent_frame
		self._obj_id = obj_id
		super(ObjectLabel, self).__init__()
		
		label_icon = QtWidgets.QLabel()
		label_icon.setPixmap(QtGui.QPixmap(":res/res/object.svg").scaledToHeight(24, QtCore.Qt.SmoothTransformation))
		self.label_text = QtWidgets.QLabel(id_to_name(self._obj_id))
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().setSpacing(0)
		self.layout().addWidget(label_icon)
		self.layout().addWidget(self.label_text)
		self.setStyleSheet("QWidget {background-color : #dddddd;} QLabel {padding : 3px;}")
		self.setCursor(QtCore.Qt.OpenHandCursor)

	def set_id(self, obj_id):
		
		self._obj_id = obj_id
		self.label_text.setText(id_to_name(self._obj_id))
	
	def mousePressEvent(self, event):
		
		mimeData = QtCore.QMimeData()
		mimeData.setData("application/deposit", bytes(json.dumps(dict(parent = self.__class__.__name__, data = [dict(obj_id = self._obj_id)])), "utf-8"))
		
		drag = QtGui.QDrag(self)
		drag.setMimeData(mimeData)
		rect = self.rect()
		pixmap = QtGui.QPixmap(rect.size())
		self.render(pixmap, QtCore.QPoint(), QtGui.QRegion(rect))
		drag.setPixmap(pixmap)
		drag.setHotSpot(event.pos() - self.pos())
		dropAction = drag.exec(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
	
	def mouseDoubleClickEvent(self, event):
		
		self._parent_frame.on_double_click()

class ObjectFrame(PrototypeFrame, QtWidgets.QFrame):
	
	def __init__(self, parent_view):
		
		self._obj_id = "obj_id"

		super(ObjectFrame, self).__init__(parent_view)
		
		self.setAcceptDrops(True)
		
		self.setLayout(QtWidgets.QHBoxLayout())
		self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		self.obj_label = ObjectLabel(self, self._obj_id)
		self.layout().insertWidget(0, self.obj_label)
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "external":
			return DropActions.ADD_RESOURCE
		if src_parent in ["ClassList", "QueryObjView", "ExternalLstView", "ClassLabel", "MdiClass"]:
			return DropActions.ADD_DESCRIPTOR
		if src_parent == "QueryLstView":
			if "cls_id" in src_data:
				return DropActions.ADD_DESCRIPTOR
			if src_data["obj_id"] != self._obj_id:
				return DropActions.ADD_RELATION
			return None
		if src_parent in ["QueryImgView", "ObjectLabel"]:
			if src_data["obj_id"] != self._obj_id:
				return DropActions.ADD_RELATION
			return None
		if src_parent == "MdiObject":
			return DropActions.ADD_RELATION
		return None
	
	def set_object(self, obj_id):
		
		self._obj_id = obj_id
		self.obj_label.set_id(self._obj_id)
	
	def get_data(self):
		
		return dict(
			obj_id = self._obj_id,
		)
	
	def on_double_click(self):
		
		item = QtWidgets.QTableWidgetItem(0)
		item.setData(QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = dict(obj_id = self._obj_id)))
		self._parent_view.on_activated(item)
	
	def on_drag_move(self, source, target, event):
		
		self.setStyleSheet("ObjectFrame {border: 1px solid black;}")
	
	def on_drag_leave(self, event):
		
		self.setStyleSheet("ObjectFrame {border: none;}")
	
	def on_drop(self, event):
		
		self.setStyleSheet("ObjectFrame {border: none;}")
