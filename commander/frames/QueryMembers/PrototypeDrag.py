from deposit.store.Worldfiles import (save_worldfile)
from deposit.store.Projections import (save_raster_projection)
from PySide2 import (QtWidgets, QtCore)
import shutil
import json
import os

class PrototypeDragModel(object):
	
	def supportedDragActions(self):
		
		return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction | QtCore.Qt.LinkAction | QtCore.Qt.ActionMask | QtCore.Qt.IgnoreAction
	
	def supportedDropActions(self):
		
		return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction | QtCore.Qt.LinkAction | QtCore.Qt.ActionMask | QtCore.Qt.IgnoreAction
	
	def flags(self, item):
		
		flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		
		if item is None:
			return flags
		
		if self.drag_supported(item):
			flags = flags | QtCore.Qt.ItemIsDragEnabled
		
		if self.drop_supported(item):
			flags = flags | QtCore.Qt.ItemIsDropEnabled
		
		if not item.is_read_only():
			flags = flags | QtCore.Qt.ItemIsEditable
		
		return flags
	
	def mimeTypes(self):
		
		return ["application/deposit", "text/uri-list", "text/plain"]
	
	def mimeData(self, indexes):
		
		data = QtCore.QMimeData()
		paths = []
		elements = []
		for index in indexes:
			item = index.data(QtCore.Qt.UserRole)
			elements.append(item.element.to_dict())
			elements[-1]["identifier"] = self.model.identifier
			elements[-1]["connstr"] = self.model.connstr
			if item.is_resource():
				filename = item.element.label.filename
				f_src = item.element.label.open()
				if f_src is None:
					continue
				else:
					tgt_path = os.path.join(self.model.files.get_temp_path(), filename)
					f_tgt = open(tgt_path, "wb")
					shutil.copyfileobj(f_src, f_tgt)
					f_src.close()
					f_tgt.close()
					paths.append(tgt_path)
				if not item.element.label.worldfile is None:
					wf_path = save_worldfile(item.element.label.worldfile, tgt_path)
					paths.append(wf_path)
				if not item.element.label.projection is None:
					proj_path = save_raster_projection(item.element.label.projection, tgt_path)
					paths.append(proj_path)
			elif item.is_geometry():
				pass # TODO handle also geometry (generate shapefile + prj)
		
		if paths:
			data.setUrls([QtCore.QUrl().fromLocalFile(path) for path in paths])
		
		data.setData("application/deposit", bytes(json.dumps(elements), "utf-8"))
		
		return data
	
	def process_drop(self, item, data):
		
		if "application/deposit" in data.formats():
			data = json.loads(data.data("application/deposit").data().decode("utf-8"))
			elements = []
			for row in data:
				if row["delement"] == "DClass":
					elements.append(self.model.classes[row["name"]])
				elif row["delement"] == "DObject":
					elements.append(self.model.objects[row["id"]])
				elif row["delement"] == "DDescriptor":
					elements.append(self.model.objects[row["target"]].descriptors[row["dclass"]])
			if elements:
				self.on_drop_elements(item, elements)
				return False
		
		if data.hasUrls():
			urls = [str(url.toString()) for url in data.urls()]
			if urls:	
				self.on_drop_url(item, urls)
				return False
		
		if data.hasText():
			self.on_drop_text(item, data.text())
			return False
		
		return False
	
	def dropMimeData(self, data, action, row, column, parent):
		
		item = parent.data(QtCore.Qt.UserRole)
		if item is None:
			return False
		return self.process_drop(item, data)
	
	def drag_supported(self, item):
		# re-implement to evaluate whether item supports drag
		# item: QueryItem
		
		return True
	
	def drop_supported(self, item):
		# re-implement to evaluate whether item supports drop
		# item: QueryItem
		
		return True
	
	def on_drop_url(self, item, urls):
		# re-implement to process drop of an url
		# item: QueryItem
		
		pass
		
	def on_drop_text(self, item, text):
		# re-implement to process drop of a text
		# item: QueryItem
		
		pass
		
	def on_drop_elements(self, item, elements):
		# re-implement to process drop of a list of DElement
		# item: QueryItem
		# elements: [DElement, ...]
		
		pass
	
class PrototypeDragView(object):
	
	def set_up_drag_drop(self):

		self.setAcceptDrops(True)
		self.setDragEnabled(True)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
		self.setDefaultDropAction(QtCore.Qt.CopyAction)
		self.setDropIndicatorShown(True)

class PrototypeDragWidget(PrototypeDragModel, PrototypeDragView):
	
	def get_drag_data(self, event):
		
		data = event.mimeData()
		item = self.itemAt(event.pos())
		if item is None:
			return None, None
		item = item.data(QtCore.Qt.UserRole)
		return item, data
	
	def dragEnterEvent(self, event):
		
		item, data = self.get_drag_data(event)
		if item is None:
			event.ignore()
			return
		if self.drag_supported(item):
			event.accept()
			return
		event.ignore()
	
	def dragMoveEvent(self, event):
		
		self.dragEnterEvent(event)
	
	def dropEvent(self, event):
		
		item, data = self.get_drag_data(event)
		if item is None:
			return
		
		self.process_drop(item, data)
	
