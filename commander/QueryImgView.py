from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtWidgets, QtCore, QtGui)

def _coords_to_icon(coords, size):
	
	coords -= coords.min(axis = 0)
	coords = (coords / coords.max()) * size
	coords = coords[:,:2]
	w, h = coords.max(axis = 0)
	coords = coords * 0.9 + [w * 0.05, h * 0.05]
	path = QtGui.QPainterPath()
	path.moveTo(coords[0][0], coords[0][1])
	for point in coords:
		path.lineTo(point[0], point[1])
	pixmap = QtGui.QPixmap(w, h)
	pixmap.fill(QtCore.Qt.white)
	painter = QtGui.QPainter(pixmap)
	painter.setPen(QtGui.QPen(QtCore.Qt.black))
	painter.drawPath(path)
	painter.end()
	return QtGui.QIcon(pixmap)

class QueryImgView(PrototypeList, QtWidgets.QListWidget):

	def __init__(self, parent_view):
		
		self._populated = False
		
		super(QueryImgView, self).__init__(parent_view)

		self.setViewMode(QtWidgets.QListView.IconMode)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.setResizeMode(QtWidgets.QListView.Adjust)
		self.setWrapping(True)
		self.setFlow(QtWidgets.QListView.LeftToRight)
		self.setUniformItemSizes(True)
		
		self.itemSelectionChanged.connect(self.on_selection_changed)
		self.itemActivated.connect(self.on_activated)
		self.verticalScrollBar().valueChanged.connect(self._on_scroll)
		self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
		
		self.set_drag_and_drop_enabled()
		
		self._icon_placeholder = QtGui.QPixmap(256, 256)
		self._icon_placeholder.fill(QtCore.Qt.white)
		self._icon_placeholder = QtGui.QIcon(self._icon_placeholder)
	
	def _get_img_item(self, row):
		
		item = QtWidgets.QListWidgetItem()
		data = self._model.image_data(row)
		item.setData(QtCore.Qt.UserRole, data)
		item.setData(QtCore.Qt.DisplayRole, "%s" % (data["data"]["value"] if "value" in data["data"] else ""))
		item.setData(QtCore.Qt.DecorationRole, self._icon_placeholder)
		item.placeholder = True
		return item
	
	def _populate(self):
		
		if self._model.has_store() and not self._populated:
			
			self.clear()
			
			self.blockSignals(True)
			
			rows = self._model.image_count()
			for row in range(rows):
				self.addItem(self._get_img_item(row))
			
			self.blockSignals(False)
			
			self._populated = True
	
	def _count_visible(self):
		# return number of visible items (e.g. after filtering)
		
		return len([idx for idx in range(self.count()) if not self.item(idx).isHidden()])
	
	def _update_visible(self):
		# TODO self._model._parent_model -> factor out to QueryModel
		
		self.blockSignals(True)
		for index in self._visible_indexes():
			item = self.itemFromIndex(index)
			if item.placeholder:
				data = item.data(QtCore.Qt.UserRole)
				icon = None
				filename = None
				if "coords" in data["data"]:
					icon = _coords_to_icon(data["data"]["coords"], 256)
				else:
					path, filename, _, thumbnail_path = self._model._parent_model.store.resources.thumbnail(data["data"]["value"], 256, data["data"]["storage_type"])
					icon = QtGui.QIcon(thumbnail_path)
				if not icon is None:
					item.setData(QtCore.Qt.DecorationRole, icon)
				if not filename is None:
					item.setData(QtCore.Qt.DisplayRole, "%s" % (filename))
				item.placeholder = False
		self.blockSignals(False)
	
	def _on_scroll(self, pos = None):
		
		self._update_visible()
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "QueryImgView":
			return DropActions.ADD_RELATION
		if src_parent == "external":
			if self._model.is_url_image(src_data["value"]):
				return DropActions.ADD_RESOURCE
			return None
		if (("image" in src_data) and src_data["image"]) or (("geometry" in src_data) and src_data["geometry"]):
			return DropActions.ADD_DESCRIPTOR
		return None
	
	def selected(self):
		
		return [item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]
	
	def thumb_size(self):
		
		return self.iconSize().width()
	
	def set_thumb_size(self, value):
		
		self.setIconSize(QtCore.QSize(value, value))
	
	def on_set_model(self):
		
		pass
	
	def on_store_changed(self, ids):
		# TODO update on add/remove items
		
		if not self._model.has_store():
			return
		self._populate()
	
	def on_activated(self, item):
		
		self._parent_view.on_activated(item)
	
	def on_filter(self, text):
		
		keep = []
		for item in self.findItems(text, QtCore.Qt.MatchContains):
			keep.append(item)
		for idx in range(self.count()):
			item = self.item(idx)
			item.setHidden(not item in keep)
		self._parent_view.on_count_changed(len(keep))
		self._update_visible()
	
	def on_zoom(self, value):
		
		self.set_thumb_size(value)
		self._update_visible()
	
	def showEvent(self, event):
		
		self._populate()
		self._update_visible()
		super(QueryImgView, self).showEvent(event)
		self._parent_view.on_count_changed(self._count_visible())
	
	def resizeEvent(self, event):
		
		super(QueryImgView, self).resizeEvent(event)
		self._update_visible()
		
	
	