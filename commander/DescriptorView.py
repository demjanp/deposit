from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.ObjectFrame import ObjectFrame
from deposit.commander.DropActions import DropActions
from deposit.DLabel import (id_to_name)
from PyQt5 import (uic, QtCore, QtWidgets, QtGui, QtSvg, QtPrintSupport)
import os
import sys
from urllib.request import urlopen, Request
from urllib.parse import urlparse

class DescriptorView(PrototypeList, *uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "Descriptor.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	def __init__(self, parent_view):
		
		self._resource_item = None
		self._drag_crosshair_item = None
		self._prev_mouse_pos = None
		self._drag_crosshair_item = None
		self._drawing_item = None
		
		super(DescriptorView, self).__init__(parent_view)
		self.setupUi(self)
		
		self.headerFrame = QtWidgets.QFrame()
		self.headerFrame.setLayout(QtWidgets.QHBoxLayout())
		self.objectFrame = ObjectFrame(self)
		self.headerFrame.layout().setContentsMargins(3, 3, 3, 3)
		self.headerFrame.layout().addWidget(self.objectFrame)
		self.headerFrame.layout().addStretch()
		
		self.graphicsView = DescriptorGraphicsView(self)
		self.verticalLayout.addWidget(self.headerFrame)
		self.verticalLayout.addWidget(self.graphicsView)
	
	def _populate(self):
		# TODO geometry
		
		self.graphicsView.clear()
		if self._model.has_store():
			data = self._model.data()
			self.objectFrame.set_object(data["data"]["obj_id"])
			self._drag_crosshair_item = DragCrosshairItem()
			self._drawing_item = DrawingItem(self)
			img_height = 0
			
			if self._model.is_geometry():
				pass
				# TODO
			else:
				path, filename, storage_type = self._model.path()
				if path:
					self.set_title("obj(%s).%s = %s" % (id_to_name(data["data"]["obj_id"]), self._model.descriptor_name(), filename))
					if os.path.splitext(path)[-1].lower() == ".svg":
						self._resource_item = SvgItem(self, self._model, path)
					else:
						self._resource_item = PixmapItem(self, path)
					rect = self._resource_item.boundingRect()
					data["data"]["width"] = rect.width()
					data["data"]["height"] = rect.height()
					img_height = rect.height()
					self._resource_item.setData(QtCore.Qt.UserRole, data)
					self.graphicsView.add_item(self._resource_item)
					
					self._drawing_item.setData(QtCore.Qt.UserRole, data)
					self.graphicsView.add_item(self._drag_crosshair_item)
					self._drag_crosshair_item.hide()
					self.graphicsView.add_item(self._drawing_item)
					for obj_id, rel_id, cls_id, descriptor, coords, typ, srid in self._model.geotags():
						self._add_geotag(obj_id, rel_id, cls_id, descriptor, coords, typ, srid, img_height)
	
	def _add_geotag(self, obj_id, rel_id, cls_id, descriptor, coords, typ, srid, image_height):
		
		item = GeotagItem(self, "obj(%s).%s" % (id_to_name(obj_id), descriptor), typ, coords, srid, image_height)
		data = dict(
			parent = self.__class__.__name__,
			data = dict(
				obj_id = obj_id,
				rel_id = rel_id,
			)
		)
		item.setData(QtCore.Qt.UserRole, data)
		self.graphicsView.add_item(item)
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "QueryLstView":
			if "cls_id" in src_data:
				if (("image" in src_data) and src_data["image"]) or (("geometry" in src_data) and src_data["geometry"]):
					return DropActions.ADD_DESCRIPTOR
				return None
			return DropActions.ADD_GEOTAG
		if (src_parent in ["QueryObjView", "ExternalLstView"]) and ((("image" in src_data) and src_data["image"]) or (("geometry" in src_data) and src_data["geometry"])):
			return DropActions.ADD_DESCRIPTOR
		if src_parent in ["QueryImgView", "ObjectLabel", "MdiObject"]:
			return DropActions.ADD_GEOTAG
		if src_parent == "external":
			if self._model._parent_model.store.resources.is_external_image(src_data["value"]):
				return DropActions.ADD_RESOURCE
		return None
	
	def set_status(self, text, timeout = 0):
		
		self.statusBar.showMessage(text, timeout)
	
	def is_drawing(self):
		
		return self._drawing_item.is_drawing()
	
	def selected(self):
		
		ret = self.graphicsView.selected()
		if ret:
			return ret
		return [self._model.data()]
	
	def on_set_model(self):
		
		self._populate()
	
	def on_store_changed(self, ids):
		
		if ids:
			data = self._resource_item.data(QtCore.Qt.UserRole)
			rel_id = data["data"]["rel_id"]
			obj_id = data["data"]["obj_id"]
			uri = data["data"]["value"]
			if (rel_id in ids["updated"]) or (obj_id in ids["updated"]) or (uri in ids["updated"]):
				self._populate()
		else:
			self._populate()
	
	def on_activated(self, item):
		
		data = item.data(QtCore.Qt.UserRole)
		if data["parent"] == "ObjectFrame":
			self._parent_view.open_object(data["data"]["obj_id"])
			return
		if "rel_id" in data["data"]:
			rel_id_own = None
			if self._resource_item:
				rel_id_own = self._resource_item.data(QtCore.Qt.UserRole)["data"]["rel_id"]
			if data["data"]["rel_id"] != rel_id_own:
				self._parent_view.open_object(data["data"]["obj_id"])
				return
			self._parent_view.open_resource(data["data"]["obj_id"], data["data"]["rel_id"])
	
	def on_changed(self, item):
		# TODO
		
		pass
	
	def on_geotag_hover(self, label):
		
		if label:
			self.set_status("Geotag: %s" % label)
		else:
			self.set_status("")
	
	def on_drag_enter(self, source, target, event):
		
		if not self._drawing_item.is_drawing():
			self._drag_crosshair_item.update(event.pos(), self._resource_item.boundingRect())
			self._drag_crosshair_item.show()
	
	def on_drag_move(self, source, target, event):
		
		if not self._drawing_item.is_drawing():
			self._drag_crosshair_item.update(event.pos(), self._resource_item.boundingRect())
		
	def on_drop(self, event):
		
		self._drag_crosshair_item.hide()
	
	def on_mouse_enter(self):
		
		self._drawing_item.set_paused(False)
	
	def on_mouse_move(self, pos):
		
		if self._drawing_item.is_drawing():
			self._drawing_item.update(pos)
	
	def on_mouse_leave(self):
		
		self._drag_crosshair_item.hide()
		self._drawing_item.set_paused(True)
	
	def on_mouse_press(self, pos, button):
		
		if self._drawing_item.is_drawing() and (button == QtCore.Qt.LeftButton):
			self._drawing_item.add_point(pos)
	
	def on_mouse_release(self, pos, button):
		# TODO
		
		pass
	
	def on_actionZoomIn_triggered(self, state):
		
		self.graphicsView.zoom(1)
	
	def on_actionZoomOut_triggered(self, state):
		
		self.graphicsView.zoom(-1)
	
	def on_actionResetZoom_triggered(self, state):
		
		self.graphicsView.zoom()
	
	def on_actionGeotagPoly_toggled(self, state):
		
		self._drawing_item.set_drawing_enabled(state)
	
	def on_actionRemoveGeotag_triggered(self, state):
		
		rel_ids = [data["data"]["rel_id"] for data in self.selected()]
		if rel_ids:
			reply = QtWidgets.QMessageBox.question(self._parent_view, "Remove Geotags?", ("Remove the %d selected Geotags?" % (len(rel_ids))) if (len(rel_ids) > 1) else "Remove the selected Geotag?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
			if reply == QtWidgets.QMessageBox.Yes:
				self._model.remove_geotags(rel_ids)
	
	def itemAt(self, pos):
		
		pos = self._resource_item.deviceTransform(self.graphicsView.viewportTransform()).map(pos)
		
		visible = self._drag_crosshair_item.isVisible()
		if visible:
			self._drag_crosshair_item.hide()
		item = self.graphicsView.itemAt(QtCore.QPoint(int(pos.x()), int(pos.y())))
		if visible:
			self._drag_crosshair_item.show()
		return item
		
	def setCurrentItem(self, item):
		# TODO
		# used to highlight drop target
		
		pass
	
	def hasFocus(self):
		
		return self.graphicsView.hasFocus()
	
	def showEvent(self, event):
		
		super(DescriptorView, self).showEvent(event)
		parent = self.parent_subwindow()
		if not parent is None:
			parent.adjustSize()
			self.graphicsView.zoom()
	

class DragCrosshairItem(QtWidgets.QGraphicsPathItem):
	
	def __init__(self):
		
		super(DragCrosshairItem, self).__init__()
	
	def update(self, pos, rect):
		
		x, y = pos.x(), pos.y()
		x0, x1, y0, y1 = rect.left(), rect.right(), rect.bottom(), rect.top()
		path = QtGui.QPainterPath()
		self.setPen(QtGui.QPen(QtCore.Qt.green))
		path.moveTo(x, y0)
		path.lineTo(x, y1)
		path.moveTo(x0, y)
		path.lineTo(x1, y)
		self.setPath(path)
		self.setZValue(3)


class DrawingItem(QtWidgets.QGraphicsPathItem):
	
	def __init__(self, parent_view):
		
		self._parent_view = parent_view
		self._is_drawing = False
		self._coords = []
		self._paused = False
		
		super(DrawingItem, self).__init__()
		
		self.setAcceptHoverEvents(True)
		self.setAcceptDrops(True)
		self.setZValue(10)
	
	def is_drawing(self):
		
		return self._is_drawing
	
	def set_drawing_enabled(self, state):
		
		self._is_drawing = state
		if state:
			self.update()
		else:
			self.clear()
	
	def update(self, pos = None):
		
		if self._coords:
			path = QtGui.QPainterPath()
			self.setPen(QtGui.QPen(QtCore.Qt.green))
			self.setBrush(QtGui.QColor(0, 255, 0, 128))
			path.moveTo(self._coords[0][0], self._coords[0][1])
			for point in self._coords[1:]:
				path.lineTo(point[0], point[1])
			if (not pos is None) and (not self._paused):
				path.lineTo(pos.x(), pos.y())
			self.setPath(path)
			self.setZValue(2)
		data = self.data(QtCore.Qt.UserRole)
		data["data"]["coords"] = [[coord[0], data["data"]["height"] - coord[1]] for coord in self._coords]
		self.setData(QtCore.Qt.UserRole, data)
	
	def set_paused(self, state):
		
		self._paused = state
		self.update()
	
	def add_point(self, pos):
		
		self._coords.append([pos.x(), pos.y()])
		self.update()
	
	def clear(self):
		
		self._coords = []
		self.setPath(QtGui.QPainterPath())

	def dragEnterEvent(self, event):
		
		self._parent_view.dragEnterEvent(event)
	
	def dragMoveEvent(self, event):
		
		self._parent_view.dragMoveEvent(event)
	
	def dropEvent(self, event):
		
		self._parent_view.dropEvent(event)


class GeotagItem(QtWidgets.QGraphicsPathItem):
	
	def __init__(self, parent_view, label, typ, coords, srid, image_height, markersize = 16):
		
		self._parent_view = parent_view
		self._label = label
		self._typ = typ
		self._coords = coords
		self._srid = srid
		self._image_height = image_height
		self._markersize = markersize
		
		super(GeotagItem, self).__init__()
		
		self.setAcceptHoverEvents(True)
		
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
		self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.setToolTip(label)
		
		if self._typ == "POINT":
			self.setPos(self._coords[0][0], self._coords[0][1])
			self.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))
		else:
			coords = self._coords.copy()
			coords[:,1] = self._image_height - coords[:,1]
			path = QtGui.QPainterPath()
#			self.setPen(QtGui.QPen(QtCore.Qt.yellow))
			self.setPen(QtGui.QPen(QtCore.Qt.red))
#			self.setBrush(QtGui.QColor(255, 255, 0, 128))
			self.setBrush(QtGui.QColor(255, 0, 0, 128))
			path.moveTo(coords[0][0], coords[0][1])
			for point in coords[1:]:
				path.lineTo(point[0], point[1])
			path.lineTo(coords[0][0], coords[0][1])
			self.setPath(path)
		self.setZValue(1)
	
	def paint(self, painter, option, widget):
		
		super(GeotagItem, self).paint(painter, option, widget)
		if self._typ == "POINT":
			
			transform = self.deviceTransform(self.scene().views()[0].viewportTransform())
			pos = self.boundingRect().center()
			hf, vf = transform.m11(), transform.m22()
			path = QtGui.QPainterPath()
			path.moveTo(pos.x(), pos.y())
			s = self._markersize // 2
			path.lineTo(pos.x() - s / hf, pos.y() - s / vf)
			path.lineTo(pos.x() - s / hf, pos.y() + s / vf)
			path.lineTo(pos.x() + s / hf, pos.y() + s / vf)
			path.lineTo(pos.x() + s / hf, pos.y() - s / vf)
			path.lineTo(pos.x() - s / hf, pos.y() - s / vf)
			self.setPath(path)
			pos = transform.map(QtCore.QPoint(0,0))
#			painter.setPen(QtGui.QPen(QtCore.Qt.yellow))
			painter.setPen(QtGui.QPen(QtCore.Qt.red))
			painter.setFont(QtGui.QFont("Arial", self._markersize))
			painter.resetTransform()
			painter.drawText(QtCore.QRectF(pos.x() - s, pos.y() - s, self._markersize, self._markersize), QtCore.Qt.AlignCenter, "+")
	
	def hoverEnterEvent(self, event):
		
		self._parent_view.on_geotag_hover(self._label)
	
	def hoverLeaveEvent(self, event):
		
		self._parent_view.on_geotag_hover("")


class ResourceItem(object):
	
	def __init__(self, parent_view, *args):
		
		self._parent_view = parent_view
		
		super(ResourceItem, self).__init__(*args)
		
		self.setAcceptHoverEvents(True)
		self.setAcceptDrops(True)
		self.setZValue(0)
	
	def hoverEnterEvent(self, event):
		
		self._parent_view.on_mouse_enter()
	
	def hoverMoveEvent(self, event):
		
		self._parent_view.on_mouse_move(event.pos())
		super(ResourceItem, self).hoverMoveEvent(event)
	
	def hoverLeaveEvent(self, event):
		
		self._parent_view.on_mouse_leave()
	
	def dragEnterEvent(self, event):
		
		self._parent_view.dragEnterEvent(event)
	
	def dragMoveEvent(self, event):
		
		self._parent_view.dragMoveEvent(event)
	
	def dropEvent(self, event):
		
		self._parent_view.dropEvent(event)
	
	def mousePressEvent(self, event):
		
		self._parent_view.on_mouse_press(event.pos(), event.button())
		super(ResourceItem, self).mousePressEvent(event)
	
	def mouseReleaseEvent(self, event):
		
		self._parent_view.on_mouse_release(event.pos(), event.button())
		super(ResourceItem, self).mouseReleaseEvent(event)
	

class PixmapItem(ResourceItem, QtWidgets.QGraphicsPixmapItem):
	
	def __init__(self, parent_view, path):
		
		scheme = urlparse(path).scheme
		if scheme in ["http", "https"]:
			pixmap = QtGui.QPixmap()
			try:
				with urlopen(Request(path, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0"})) as data:
					pixmap.loadFromData(data.read())
				data.close()
			except:
				print("PixmapItem.__init__", sys.exc_info())
		else:
			pixmap = QtGui.QPixmap(path)
		super(PixmapItem, self).__init__(parent_view, pixmap)


class SvgItem(ResourceItem, QtSvg.QGraphicsSvgItem):
	
	def __init__(self, parent_view, model, path):
		
		path, filename, storage_type = model.store.resources.get_path(path)
		online = (storage_type in [model.store.resources.RESOURCE_ONLINE, model.store.resources.RESOURCE_CONNECTED_ONLINE])
		if online:
			path = model.store.file.make_temp_copy(path, filename, online = True)
		super(SvgItem, self).__init__(parent_view, path)


class DescriptorGraphicsView(QtWidgets.QGraphicsView):
	
	def __init__(self, parent_view):
	
		self._parent_view = parent_view
		self._scene = None
		self._scene_rect = None
		
		super(DescriptorGraphicsView, self).__init__()
		
		self._scene = QtWidgets.QGraphicsScene()
		self._scene.selectionChanged.connect(self._parent_view.on_selection_changed)
		
		self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
		self.setScene(self._scene)
	
	def add_item(self, item):
		
		self._scene.addItem(item)
		self.zoom()
	
	def clear(self):
		
		self._scene.clear()
	
	def zoom(self, direction = None):
		
		if direction is None:
			rect = self._scene.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(10, 10, 10, 10))
			self.setSceneRect(rect)
			self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
		else:
			if direction == 1:
				factor = 1.1
			elif direction == -1:
				factor = 0.9
			self.scale(factor, factor)
	
	def selected(self):
		
		return [item.data(QtCore.Qt.UserRole) for item in self._scene.selectedItems()]
	
	def wheelEvent(self, event):
		
		d = event.angleDelta().y()
		if d > 0:
			self.zoom(1)
		elif d < 0:
			self.zoom(-1)
	
	def showEvent(self, event):
		
		self.zoom()
	
	def resizeEvent(self, event):
		
		if self._scene_rect is None:
			self.zoom()
			self._scene_rect = self.rect()
		else:
			new_rect = self.rect()
			factor = max(new_rect.width() / self._scene_rect.width(), new_rect.height() / self._scene_rect.height())
			self.scale(factor, factor)
			self._scene_rect = new_rect
	
	def mouseDoubleClickEvent(self, event):
		
		item = self.itemAt(event.pos())
		if item:
			self._parent_view.on_activated(item)
	
	def mouseReleaseEvent(self, event):
		
		self._parent_view.on_mouse_release(event.pos(), event.button())
		super(DescriptorGraphicsView, self).mouseReleaseEvent(event)

