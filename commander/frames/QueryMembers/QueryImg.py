from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryItem import (QueryItem)
from deposit.commander.frames.QueryMembers.QuerySelection import (QuerySelection)
from deposit.commander.frames.QueryMembers.PrototypeDrag import (PrototypeDragView, PrototypeDragModel)

from PySide2 import (QtWidgets, QtCore, QtGui)
from natsort import (natsorted)

class ImageDelegate(QtWidgets.QStyledItemDelegate):
	
	def __init__(self, parent):
		
		self.parent = parent
		
		QtWidgets.QStyledItemDelegate.__init__(self, parent)
	
	def paint(self, painter, option, index):
		
		item = index.data(QtCore.Qt.UserRole)
		self.parent.list_model.on_paint(item)
		
		QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

class IconThread(QtCore.QThread):
	
	def __init__(self, parent, item, icon_size = 256):
		
		self.parent = parent
		self.index = item.index
		self.label = item.element.label
		self.icon_size = icon_size
		self.local_folder = self.parent.model.local_folder
		
		if item.element.linked:
			self.local_folder = self.parent.model.linked[item.element.linked.split("#")[0] + "#"].local_folder
		
		QtCore.QThread.__init__(self)
	
	def run(self):
		
		path = self.parent.model.images.get_thumbnail(self.label, size = self.icon_size, root_folder = self.local_folder)
		self.parent.on_icon_thread(self.index, path)

class QueryImgLazy(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		self.has_image = False
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		def has_image():
			
			for row in self.query:
				for column in row:
					descriptor = row[column].descriptor
					if not descriptor is None:
						if (descriptor.label.__class__.__name__ == "DResource") and descriptor.label.is_image():
							return True
			return False

		self.has_image = has_image()
	
	def set_up(self):
		
		pass
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def get_row_count(self):
		
		return int(self.has_image)
	
class ProxyModel(QtCore.QSortFilterProxyModel):
	
	def __init__(self, list_view):
		
		self.list_view = list_view
		
		super(ProxyModel, self).__init__()
	
	def lessThan(self, source_left, source_right):
		
		def get_row(source):
			
			obj_id = None
			element = source.data(QtCore.Qt.UserRole).element
			if element.__class__.__name__ == "DObject":
				obj_id = element.id
			elif element.__class__.__name__ == "DDescriptor":
				obj_id = element.target.id
			if (obj_id is not None) and (obj_id in self.list_view.row_ids):
				return self.list_view.row_ids[obj_id]
			return source.data(QtCore.Qt.DisplayRole)
		
		values = [("" if val is None else val) for val in [get_row(source_left), get_row(source_right)]]
		
		return values == natsorted(values)
	
	def sort(self):
		
		QtCore.QSortFilterProxyModel.sort(self, 0, QtCore.Qt.DescendingOrder)
		QtCore.QSortFilterProxyModel.sort(self, 0, QtCore.Qt.AscendingOrder)
	
class ListModel(DModule, PrototypeDragModel, QtCore.QAbstractListModel):
	
	icon_loaded = QtCore.Signal(QtCore.QModelIndex)
	
	def __init__(self, model, view, query, list_view, icon_size = 256):
		
		self.model = model
		self.view = view
		self.query = query
		self.icon_size = icon_size
		self.images = [] # [DDescriptor, ...]
		self.icons = [] # [QIcon or None, ...]; for each image
		self.empty_icon = None
		
		self.proxy_model = None
		self.threads = {} # {row: IconThread, ...}

		DModule.__init__(self)
		QtCore.QAbstractListModel.__init__(self)
		
		for row in self.threads:
			self.threads[row].terminate()
			self.threads[row].wait()
		self.threads = {}
		
		pixmap = QtGui.QPixmap(self.icon_size, self.icon_size)
		pixmap.fill()
		self.empty_icon = QtGui.QIcon(pixmap)
		
		self.images = []
		done = set()
		for row in self.query:
			for column in row:
				descriptor = row[column].descriptor
				if descriptor is None:
					continue
				if descriptor.label.value in done:
					continue
				if (descriptor.label.__class__.__name__ == "DResource") and descriptor.label.is_image():
					self.images.append(descriptor)
					done.add(descriptor.label.value)
		self.icons = [None] * len(self.images)
		
		self.proxy_model = ProxyModel(list_view)
		self.proxy_model.setSourceModel(self)
		
		self.proxy_model.sort()
		
	def rowCount(self, parent):
		
		return len(self.images)
	
	def flags(self, index):
		
		item = self.data(index, QtCore.Qt.UserRole)
		
		return PrototypeDragModel.flags(self, item)
	
	def data(self, index, role):
		
		if role == QtCore.Qt.DisplayRole:
			return self.images[index.row()].label.filename
		
		if role == QtCore.Qt.DecorationRole:
			icon = self.icons[index.row()]
			if icon is None:
				return self.empty_icon
			return icon
		
		if role == QtCore.Qt.UserRole:
			return QueryItem(index, self.images[index.row()])
		
		return None
	
	def on_icon_thread(self, index, path):
		
		if not path is None:
			self.icons[index.row()] = QtGui.QIcon(path)
			self.icon_loaded.emit(self.proxy_model.mapFromSource(index))
				
	def on_paint(self, item):
		
		if item is None:
			return
		
		row = item.index.row()
		if (self.icons[row] is None) and (not row in self.threads):
			self.threads[row] = IconThread(self, item, self.icon_size)
			self.threads[row].start()
	
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

class QueryImg(Frame, PrototypeDragView, QtWidgets.QListView):
	
	def __init__(self, model, view, parent, query, icon_size = 256):
		
		self.query = query
		self.icon_size = icon_size
		self.list_model = None
		self.row_ids = {}  # {object id: row, ...}
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QListView.__init__(self, parent)
		
		self.set_up()
		self.set_up_drag_drop()
	
	def set_up(self):
		
		self.setItemDelegate(ImageDelegate(self))
		
		self.list_model = ListModel(self.model, self.view, self.query, self, self.icon_size)
		
		self.setViewMode(QtWidgets.QListView.IconMode)
		self.setUniformItemSizes(True)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.setResizeMode(QtWidgets.QListView.Adjust)
		self.setWrapping(True)
		self.setFlow(QtWidgets.QListView.LeftToRight)
		
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		
		self.setModel(self.list_model.proxy_model)
		
		try: self.activated.disconnect()
		except: pass
		self.activated.connect(self.on_activated)
		
		self.list_model.icon_loaded.connect(self.on_icon_loaded)
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def filter(self, text):
		
		if text == "":
			self.list_model.proxy_model.setFilterWildcard("")
		else:
			self.list_model.proxy_model.setFilterRegExp(QtCore.QRegExp(".*%s.*" % text, QtCore.Qt.CaseInsensitive))
		self.list_model.proxy_model.setFilterKeyColumn(-1)
	
	def set_row_ids(self, row_ids):
		
		self.row_ids = row_ids.copy()
		
		self.list_model.proxy_model.sort()
	
	def set_thumbnail_size(self, value):
		
		self.setIconSize(QtCore.QSize(value, value))
	
	def get_row_object(self, row):
		
		element = self.list_model.proxy_model.data(self.list_model.proxy_model.index(row, 0), QtCore.Qt.UserRole).element
		if element.__class__.__name__ == "DObject":
			return element
		if element.__class__.__name__ == "DDescriptor":
			return element.target
	
	def get_selected(self):
		
		return QuerySelection(self.model, self.view, self.selectionModel().selectedIndexes())
#		return [[index.data(QtCore.Qt.UserRole) for index in self.selectionModel().selectedIndexes()]]
	
	def get_selected_objects(self):
		# return {row: DObject, ...}
		
		return dict([(row, self.get_row_object(row)) for row in self.get_selected().rows()])
	
	def get_row_count(self):
		
		return self.list_model.proxy_model.rowCount()
	
	def get_mime_data(self, indexes):
		
		return self.list_model.mimeData(indexes)
	
	def on_activated(self, index):
		
		item = index.data(QtCore.Qt.UserRole)
		self.broadcast(Broadcasts.VIEW_DESCRIPTOR_ACTIVATED, item.element)
		
	def selectionChanged(self, selected, deselected):
		
		super(QueryImg, self).selectionChanged(selected, deselected)
		
		selected = self.get_selected()
		if len(selected):
			self.parent.tab_lst.select_object(selected[0][0].element.target)
		
#		self.broadcast(Broadcasts.VIEW_SELECTED)
#		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def focusInEvent(self, event):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
		super(QueryImg, self).focusInEvent(event)
	
	def focusOutEvent(self, event):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
		super(QueryImg, self).focusOutEvent(event)
	
	def on_icon_loaded(self, index):
		
		self.update(index)


