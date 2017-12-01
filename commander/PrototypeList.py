from deposit.commander.MdiArea import MdiSubWindow
from PyQt5 import (QtWidgets, QtCore, QtGui)
from urllib.parse import urlparse
import numpy as np
import json
import sys
import os

class PrototypeList(object):
	
	def __init__(self, parent_view):
		
		self._parent_view = parent_view
		self._model = None
		
		super(PrototypeList, self).__init__()
		
		self._parent_view.action.connect(self._eval_action)
	
	def _items_to_data(self, items):
		
		data = []
		for item in items:
			if item is None:
				continue
			if isinstance(item, QtWidgets.QTreeWidgetItem):
				item_data = item.data(0, QtCore.Qt.UserRole)
			else:
				item_data = item.data(QtCore.Qt.UserRole)
			if item_data:
				data.append(item_data["data"])
		ret = dict(parent = self.__class__.__name__, data = data if data else [{}])		
		if hasattr(self._model, "has_relation") and self._model.has_relation() and (not data):
			ret["data"] = [self._model.relation()]
		if hasattr(self._model, "parent_class") and self._model.parent_class() and (not data):
			ret["data"][0]["parent_class"] = self._model.parent_class()
		if hasattr(self, "obj_id"):
			ret["data"][0]["obj_id"] = self.obj_id()
		if hasattr(self, "cls_id"):
			ret["data"][0]["cls_id"] = self.cls_id()
		return ret
	
	def _eval_drag(self, event):
		
		source = None
		data = event.mimeData()
		if "application/deposit" in data.formats():
			source = json.loads(data.data("application/deposit").data().decode("utf-8"))
		elif data.hasUrls():
			source = dict(parent = "external", data = [dict(value = url.toString()) for url in data.urls()], paths = [])
		if not source is None:
			item = self.itemAt(event.pos())
			target = self._items_to_data([item])
			for src_data in source["data"]:
				if not self.get_drop_action(source["parent"], src_data, target["data"][0]) is None:
					self.setCurrentItem(item)
					if hasattr(event, "accept"):
						event.accept()
					return source, target
		event.ignore()
		return None, None
	
	def _eval_action(self, signal, name, args):
		# check if view has on_action[name]_[signal] implemented & try to call it with args
		
		if self.hasFocus() or (self.parent_subwindow() is None):
			fnc_name = "on_action%s_%s" % (name, signal)
			if hasattr(self, fnc_name):
				try:
					getattr(self, fnc_name)(*args)
				except:
					print("%s.%s call failed" % (self.__class__.__name__, fnc_name))
					print(sys.exc_info())
	
	def _visible_indexes(self):
		
		ret = []
		rect = self.viewport().contentsRect()
		top = self.indexAt(rect.topLeft())
		if top.isValid():
			is_table = hasattr(self, "rowCount")
			bottom = self.indexAt(rect.bottomLeft())
			if is_table:
				count = self.rowCount()
			else:
				count = self.count()
			if not bottom.isValid():
				if is_table:
					bottom = self.model().index(count - 1, 0)
				else:
					bottom = self.model().index(count - 1)
			for row in range(top.row(), min(count, bottom.row() + 5)):
				if is_table:
					for column in range(self.columnCount()):
						ret.append(self.model().index(row, column))
				else:
					ret.append(self.model().index(row))
		return ret	
	
	@property
	def action(self):
		# Signal action(str, str, list); (signal, name, tuple)
		
		return self._parent_view.action
	
	def set_model(self, model):
		
		self._model = model
		self.on_set_model()
	
	def set_drag_and_drop_enabled(self):
		
		self.setAcceptDrops(True)
		self.setDragEnabled(True)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
		self.setDefaultDropAction(QtCore.Qt.LinkAction)
	
	def parent_subwindow(self):
		parent = self
		while True:
			parent = parent.parent()
			if (parent is None) or isinstance(parent, MdiSubWindow):
				break
		return parent
	
	def selected(self):
		
		return []
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		# re-implement to enable drag & drop
		# src_parent = name of parent class
		# src_data / tgt_data = dict(
		#	obj_id = obj_id,
		#	row = row,
		#	column = column,
		#	cls_id = cls_id,
		#	rel_id = rel_id,
		#	value = value,
		#	read_only = True/False,
		#	image = True/False
		#	geometry = True/False
		#	obj_id2 = obj_id (related),
		#	rel_label = label,
		#	reversed = True/False,
		#	parent_class = cls_id,
		#	coords = [[x, y], ...],
		#	path = path,
		#	filename = filename,
		#	thumbnail = thumbnail,
		# )
		# return DragAction
		
		return None
	
	def get_values(self, title, *args):
		
		return self._parent_view.get_values(title, *args)
	
	def set_title(self, title):
		
		self.setWindowTitle(title)
	
	def process_drop(self, *args):
		
		self._parent_view.process_drop(*args)
	
	def on_set_model(self):
		# called after model has been set
		
		pass
	
	def on_store_changed(self, ids):
		
		pass
	
	def on_selection_changed(self):
		
		self._parent_view.on_selection_changed()
	
	def on_widget_show(self):
		
		self._parent_view.on_widget_show()
	
	def on_widget_focus(self):
		
		self._parent_view.on_widget_focus()
	
	def on_drag_enter(self, source, target, event):
		
		pass
	
	def on_drag_move(self, source, target, event):
		
		pass
	
	def on_filter(self, text):
		
		pass
	
	def on_zoom(self, value):
		
		pass
	
	def on_drop(self, event):
		
		pass
	
	def sizeHint(self):
		
		size = super(PrototypeList, self).sizeHint()
		max_w, max_h = size.width(), size.height()
		parent = self.parent_subwindow()
		if not parent is None:
			mdi_size = parent.mdiArea().size()
			max_w = (mdi_size.width() - self.pos().x()) - 25
			max_h = (mdi_size.height() - self.pos().y()) - 25
			size.setWidth(min(size.width(), max_w))
			size.setHeight(min(size.height(), max_h))
		return size
	
	def mimeData(self, items):
		# TODO factor out self._model._parent_model... references to PrototypeListModel
		
		mime_data = super(PrototypeList, self).mimeData(items)
		data = self._items_to_data(items)
		paths = []
		for item_data in data["data"]:
			if ("storage_type" in item_data) and item_data["storage_type"]:
				path, filename, _ = self._model._parent_model.store.resources.get_path(item_data["value"], item_data["storage_type"])
				paths.append(path)
				if item_data["obj3d"]:
					for path_aux in self._model._parent_model.store.resources.material_3d(item_data["value"], item_data["storage_type"]):
						if not path_aux is None:
							paths.append(path_aux)
				elif self._model._parent_model.store.resources.has_worldfile(item_data["value"], item_data["storage_type"]):
					params = self._model._parent_model.store.resources.worldfile(item_data["value"])
					if params:
						filename, ext = os.path.splitext(path)
						filename = os.path.split(filename)[-1]
						ext = ext.lower() + "w"
						path_wf = os.path.abspath(os.path.join(self._model._parent_model.store.file.get_temp_path(), filename + ext))
						self._model._parent_model.store.file.save_worldfile(params, path_wf)
						paths.append(path_wf)
		if paths:
			mime_data.setUrls([QtCore.QUrl().fromLocalFile(path) for path in paths])
		for i, row in enumerate(data["data"]):
			for key in row:
				if isinstance(row[key], np.generic):
					data["data"][i][key] = np.asscalar(row[key])
		mime_data.setData("application/deposit", bytes(json.dumps(data), "utf-8"))
		return mime_data
	
	def dragEnterEvent(self, event):
		
		event.accept()
	
	def dragMoveEvent(self, event):
		
		source, target = self._eval_drag(event)
		if not source is None:
			self.on_drag_move(source, target, event)
	
	def dropEvent(self, event):
		
		source, target = self._eval_drag(event)
		if not source is None:
			self._parent_view.process_drop(self, source["parent"], source["data"], target["data"][0], event)
		self.on_drop(event)
	
	def showEvent(self, event):
		
		super(PrototypeList, self).showEvent(event)
		self._parent_view.on_widget_show()
	
	def focusInEvent(self, event):
		
		super(PrototypeList, self).focusInEvent(event)
		self._parent_view.on_widget_focus()
	
	
	