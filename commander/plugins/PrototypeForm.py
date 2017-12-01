from deposit.commander.plugins.PrototypePlugin import PrototypePlugin
from deposit.commander.PrototypeFrame import PrototypeFrame
from deposit.commander.DropActions import DropActions
from deposit.commander.MainWindowView import signal_handler
from deposit import (DString)
from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
from natsort import (natsorted)
import json

class RelationLabel(QtWidgets.QLabel):
	
	def __init__(self, obj_id, id, rel, cls):
		
		self._obj_id = obj_id
		self._rel = rel
		self._cls = cls
		self._id = id
		
		super(RelationLabel, self).__init__()
		
		self.setTextFormat(QtCore.Qt.RichText)
		link = "obj(%s).*" % (self._obj_id[4:])
		self.setText('''<html><head/><body><p><a href="%s"><span style=" text-decoration: underline; color:#0000ff;">%s</span></a></p></body></html>''' % (link, self._id))
	
	def rel_cls(self):
		# return relation & class label
		
		return [self._rel, self._cls]
	
class RelationFrame(PrototypeFrame, QtWidgets.QFrame):
	
	def __init__(self, parent_view, obj_id, rel_label, cls_id, reversed, vertical = False):
		
		self._obj_id = obj_id
		self._rel_label = rel_label
		self._cls_id = cls_id
		self._reversed = reversed
		self._vertical = vertical
		
		self._style_standard = "RelationFrame { border: 1px solid grey; padding: 3px; } QLabel { font: 11pt sans-serif; }"
		self._style_active = "RelationFrame { border: 2px solid black; padding: 3px; } QLabel { font: 11pt sans-serif; }"
		
		super(RelationFrame, self).__init__(parent_view)
		
		self.setAcceptDrops(True)
		
		if self._vertical:
			self.setLayout(QtWidgets.QVBoxLayout())
		else:
			self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
		filler_label = QtWidgets.QLabel()
		filler_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.layout().addWidget(filler_label)
		
		self.setStyleSheet(self._style_standard);
	
	def set_object(self, obj_id):
		
		self._obj_id = obj_id
	
	def get_data(self):
		
		return dict(
			obj_id = self._obj_id,
			cls_id = self._cls_id,
			rel_label = self._rel_label,
			reversed = self._reversed,
		)
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if (self._obj_id is None) or (self._cls_id is None):
			return None
		if (not "parent_class" in src_data) or (src_data["parent_class"] != self._cls_id):
			return None
		if src_parent in ["QueryLstView", "ToolBoxList"]:
			if src_data["obj_id"] != self._obj_id:
				return DropActions.ADD_RELATION
			return None
		if src_parent in ["QueryImgView", "ObjectLabel"]:
			if src_data["obj_id"] != self._obj_id:
				return DropActions.ADD_RELATION
			return None
		return None
	
	def on_drag_move(self, source, target, event):
		
		self.setStyleSheet(self._style_active)
	
	def on_drag_leave(self, event):
		
		self.setStyleSheet(self._style_standard)
	
	def on_drop(self, event):
		
		self.setStyleSheet(self._style_standard)

class ToolBoxList(QtWidgets.QTableWidget):
	# TODO on_store_changed
	
	def __init__(self, query, model):
		
		self._query = query
		self._model = model
		
		super(ToolBoxList, self).__init__()
		
		self.horizontalHeader().setVisible(False)
		self.verticalHeader().setVisible(False)
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		
		self.setDragEnabled(True)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
		
		self._populate()
		
	def _populate(self):
		
		qry = self._model.query(self._query)
		column_ids = [cls_id for cls_id, _ in qry.columns]
		
		self.setRowCount(len(qry.objects))
		self.setColumnCount(len(column_ids))
		
		for column in range(len(column_ids)):
			self.horizontalHeader().setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
		
		if qry.objects:
			grid = [] # [rows x columns] = [display value, data]
			for row, obj_id in enumerate(qry.objects):
				grid.append([])
				for column, col_id in enumerate(column_ids):
					cls_id = col_id.split(".")[0]
					grid[-1].append([qry[obj_id][col_id].value, dict(obj_id = obj_id, parent_class = cls_id)])
			grid = natsorted(grid, key = lambda row: row[0][0])
			
			for row in range(len(grid)):
				for column in range(len(grid[0])):
					item = QtWidgets.QTableWidgetItem()
					item.setData(QtCore.Qt.DisplayRole, grid[row][column][0])
					item.setData(QtCore.Qt.UserRole, grid[row][column][1])
					item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable)
					self.setItem(row, column, item)
		
		self.adjustSize()

	def mimeData(self, items):
		# TODO factor out self._model._parent_model... references to PrototypeListModel
		
		mime_data = super(ToolBoxList, self).mimeData(items)
		data = dict(parent = self.__class__.__name__, data = [])
		for item in items:
			if item is None:
				continue
			item_data = item.data(QtCore.Qt.UserRole)
			if item_data:
				data["data"].append(item_data)
		mime_data.setData("application/deposit", bytes(json.dumps(data), "utf-8"))
		return mime_data

class PrototypeForm(PrototypePlugin):
	
	def __init__(self, parent_view, obj_id = None, **kwargs):
		
		self._obj_id = obj_id
		self._cls_id = None
		self._cls_label = None
		self._queries = {} # {name: query, ...}
		self._relations = {} # {relation: QFrame, ...}
		self._edited = False
		
		super(PrototypeForm, self).__init__(parent_view, **kwargs)
		
		self._unlink_icon = QtGui.QIcon(":res/res/unlink.svg")
	
	def _update_submit_reset_states(self):
		
		self.buttonSubmit.setEnabled(self._edited and self.get_submit_enabled())
		self.buttonObject.setEnabled(not self._obj_id is None)
	
	def set_model(self, model):
		
		super(PrototypeForm, self).set_model(model)
		
		self._cls_label = self.windowTitle()
		self._cls_id = self._model.get_class_id(self._cls_label)
		self.set_up_relations()
		self.set_up_toolboxes()
		
		# DEBUG
		self.buttonPrevious.hide()
		self.buttonNext.hide()		
	
	def set_up_controls(self):
		
		for key in self.__dict__:
			var = self.__dict__[key]
			if isinstance(var, QtWidgets.QComboBox):
				query = var.currentText()
				if query:
					self._queries[key] = query
				var.editTextChanged.connect(signal_handler(self.on_edit, key[5:]))
				
			elif isinstance(var, QtWidgets.QLineEdit):
				query = var.text()
				if query:
					self._queries[key] = query
				var.textChanged.connect(signal_handler(self.on_edit, key[4:]))
				
			elif isinstance(var, QtWidgets.QPlainTextEdit):
				query = var.toPlainText()
				if query:
					self._queries[key] = query
				var.textChanged.connect(signal_handler(self.on_edit, key[4:]))
	
	def set_up_relations(self):
		
		for frame in self.findChildren(QtWidgets.QFrame):
			if frame.objectName().startswith("relation_"):
				label = frame.findChildren(QtWidgets.QLabel)[0]
				rel_labels = label.text().split(",")
				label.setParent(None)
				rel_label, cls_name = rel_labels[0].split(".")[:2]
				reversed = (rel_label[0] == "~")
				rel_label = rel_label.strip("~")
				cls_id = self._model.get_class_id(cls_name, create = True)
				vertical = isinstance(frame.layout(), QtWidgets.QVBoxLayout)
				rel_frame = RelationFrame(self._parent_view, self._obj_id, rel_label, cls_id, not reversed, vertical = vertical)
				frame.layout().addWidget(rel_frame)
				for relation in rel_labels:
					self._relations[relation] = rel_frame
	
	def set_up_toolboxes(self):
		
		for toolbox in self.findChildren(QtWidgets.QToolBox):
			for i in range(toolbox.count()):
				page = toolbox.widget(i)
				label = page.findChildren(QtWidgets.QLabel)[0]
				query = label.text()
				label.setParent(None)
				lst = ToolBoxList(query, self._model._parent_model)
				page.layout().setContentsMargins(0, 0, 0, 0)
				page.layout().setSpacing(0)
				page.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
				page.layout().addWidget(lst)
				page.adjustSize()
			toolbox.adjustSize()
			toolbox.currentChanged.connect(self.on_toolbox_current_changed)
			
	def update_links(self):
		
		for item in self.findChildren(QtWidgets.QLabel):
			if (item.textFormat() == QtCore.Qt.RichText) and ("<a href=" in item.text()):
				try:
					item.linkActivated.disconnect()
				except:
					pass
				item.linkActivated.connect(self.on_link_activated)
	
	def load_data(self):
		
		for key in self._queries:
			var = self.__dict__[key]
			if isinstance(var, QtWidgets.QComboBox):
				values = self._model.get_values(self._cls_id, self._obj_id, self._queries[key])
				if values:
					var.blockSignals(True)
					var.clear()
					var.addItems(values)
					var.blockSignals(False)
			elif isinstance(var, QtWidgets.QLineEdit):
				var.blockSignals(True)
				var.setText(self._model.get_value(self._obj_id, self._queries[key]))
				var.blockSignals(False)
			elif isinstance(var, QtWidgets.QPlainTextEdit):
				var.blockSignals(True)
				var.setPlainText(self._model.get_value(self._obj_id, self._queries[key]))
				var.blockSignals(False)
		
		self.clear_relations()
		self.update_relations()
		self.update_links()
		self._update_submit_reset_states()
		self.on_load_data()
	
	def set_enabled(self, descr_name, state):
		
		for key in self.__dict__:
			if key.endswith(descr_name):
				self.__dict__[key].setEnabled(state)
				return
	
	def set_obj(self, obj_id):
		
		self._obj_id = obj_id
		if self._obj_id:
			self.load_data()
		else:
			self.clear_relations()
		self._update_submit_reset_states()
	
	def set_text(self, descr_name, text):
		
		for key in self.__dict__:
			if key.endswith(descr_name) and (key.startswith("edit") or key.startswith("combo") or key.startswith("text")):
				var = self.__dict__[key]
				if isinstance(var, QtWidgets.QComboBox):
					var.blockSignals(True)
					values = self._model.get_values(self._cls_id, self._obj_id, self._queries[key])
					values = [text] + [val for val in values if val != text]
					var.clear()
					var.addItems(values)
					var.blockSignals(False)
				elif isinstance(var, QtWidgets.QLineEdit):
					var.blockSignals(True)
					var.setText(text)
					var.blockSignals(False)
				elif isinstance(var, QtWidgets.QPlainTextEdit):
					var.blockSignals(True)
					var.setPlainText(text)
					var.blockSignals(False)
	
	def get_descriptor_name(self, key):
		
		if key.startswith("edit") and isinstance(self.__dict__[key], QtWidgets.QLineEdit):
			return key[4:]
		if key.startswith("combo") and isinstance(self.__dict__[key], QtWidgets.QComboBox):
			return key[5:]
		if key.startswith("text") and isinstance(self.__dict__[key], QtWidgets.QPlainTextEdit):
			return key[4:]
		return None
	
	def get_descriptor_names(self):
		
		res = []
		for key in self.__dict__:
			name = self.get_descriptor_name(key)
			if name:
				res.append(name)
		return res
	
	def get_text_key(self, key):
		
		var = self.__dict__[key]
		if isinstance(var, QtWidgets.QComboBox):
			return var.lineEdit().text()
		elif isinstance(var, QtWidgets.QLineEdit):
			return var.text()
		elif isinstance(var, QtWidgets.QPlainTextEdit):
			return var.toPlainText()
		return ""
	
	def get_text(self, descr_name):
		
		for key in self.__dict__:
			if key.endswith(descr_name) and (key.startswith("edit") or key.startswith("combo") or key.startswith("text")):
				return self.get_text_key(key)
		return ""
	
	def get_submit_enabled(self):
		# re-implement to check whether the Submit button should be enabled
		
		return False
	
	def get_merge(self, descr_name):
		# re-implement to check whether Descriptor should be merged
		
		return False
	
	def clear_relations(self):
		
		for frame in self.findChildren(RelationFrame):
			layout = frame.layout()
			for i in reversed(range(layout.count())):
				item = layout.itemAt(i)
				widget = item.widget()
				if isinstance(widget, RelationLabel) or isinstance(widget, QtWidgets.QToolButton):
					widget.setParent(None)
	
	def update_relations(self):
	
		for relation in self._relations:
			self._relations[relation].set_object(self._obj_id)
			related = self._model.get_related(self._obj_id, relation) # [[obj_id, rel_id, Id], ...]
			if related:
				for obj_id, id, rel, cls in related:
					item = RelationLabel(obj_id, id, rel, cls)
					self._relations[relation].layout().insertWidget(0, item)
				button = QtWidgets.QToolButton()
				button.setIcon(self._unlink_icon)
				button.clicked.connect(signal_handler(self.on_unlink, relation))
				self._relations[relation].layout().addWidget(button)
	
	def clear_descriptors(self):
		
		for name in self.get_descriptor_names():
			self.set_text(name, "")
	
	def reset(self):
		
		self.clear_descriptors()
		self.clear_relations()
		self._update_submit_reset_states()
		self.on_reset()
	
	def on_set_model(self):
		
		pass
	
	def on_show(self):
		
		if self._cls_id is None:
			return
		if self._obj_id is None:
			selected = self._parent_view.selected()
			for data in selected:
				if ("obj_id" in data["data"]) and data["data"]["obj_id"]:
					if self._obj_id is None:
						self._obj_id = data["data"]["obj_id"]
					else:
						self._obj_id = None
						break
		if self._obj_id and not self._model.is_member(self._obj_id, self._cls_id):
			self._obj_id = None
		
		self.set_up_controls()
		self.load_data()
	
	def on_edit(self, descr_name, *args):
		
		self._edited = True
		self._update_submit_reset_states()
	
	def on_load_data(self):
		
		pass
	
	def on_store_changed(self, ids):
		
		self.clear_relations()
		self.update_relations()
		self.update_links()
	
	def on_submit(self):
	
		pass
	
	def on_reset(self):
		
		pass
	
	def on_toolbox_current_changed(self, index):
		
		for toolbox in self.findChildren(QtWidgets.QToolBox):
			for i in range(toolbox.count()):
				toolbox.widget(i).adjustSize()
			toolbox.adjustSize()
		size = self.window().size()
		self.window().resize(self.window().sizeHint())
		self.window().resize(size)
	
	def on_unlink(self, relation, *args):
		
		to_delete = [] # [[obj_id, rel, cls], ...]
		layout = self._relations[relation].layout()
		for i in range(layout.count()):
			item = layout.itemAt(i)
			widget = item.widget()
			if isinstance(widget, RelationLabel):
				rel, cls = widget.rel_cls()
				row = [self._obj_id, rel, cls]
				if not row in to_delete:
					to_delete.append(row)
		self._model.delete_relations(to_delete)
	
	def on_close(self):
		
		pass
	
	@QtCore.pyqtSlot()
	def on_buttonPrevious_clicked(self):
		
		print("previous") # DEBUG
	
	@QtCore.pyqtSlot()
	def on_buttonNext_clicked(self):
		
		print("next") # DEBUG
	
	@QtCore.pyqtSlot()
	def on_buttonSubmit_clicked(self):
		
		fields = [] # [name, ...]
		targets = [] # [traverse, ...]; traverse: C.D / C.R.C.D
		merges = [] # [True/False, ...]; in order of fields
		data = [{}] # [{column: DLabel, ...}, ...]; in order of rows
		column = 0
		for key in self._queries:
			label = self.get_text_key(key)
			if label:
				fields.append(key)
				merges.append(self.get_merge(self.get_descriptor_name(key)))
				targets.append("%s.%s" % (self._cls_label, self._queries[key]))
				data[0][column] = DString(label)
				column += 1
		self._model.import_data(data, fields, targets, merges)
		self._edited = False
		self.on_submit()
	
	@QtCore.pyqtSlot()
	def on_buttonReset_clicked(self):
		
		self.reset()
	
	@QtCore.pyqtSlot(str)
	def on_link_activated(self, link):
		
		plugins = self._parent_view.get_plugins() # {name: label, ...}
		link_tst = "".join([ch for ch in link if not ch.isnumeric()])
		if link_tst == "obj().*":
			obj_id = "obj_%s" % ("".join([ch for ch in link if ch.isnumeric()]))
			cls_ids = self._model._parent_model.store.members.get_parents(obj_id)
			for cls_id in cls_ids:
				class_name = self._model._parent_model.store.get_label(cls_id).value
				for plugin_name in plugins:
					if plugins[plugin_name] == class_name:
						self._parent_view.open_plugin(plugin_name, obj_id = obj_id)
						return
		
		if self._obj_id:
			link = link.replace("$(obj)", "obj(%s)" % (self._obj_id[4:]))
		for key in self._queries:
			link = link.replace("$(%s)" % (self._queries[key]), self.get_text_key(key))
		self._parent_view.open_query(link)
		self._parent_view.activateWindow()
		self._parent_view.raise_()
	
	@QtCore.pyqtSlot()
	def on_buttonObject_clicked(self):
		
		self._parent_view.open_object(self._obj_id)
		self._parent_view.activateWindow()
		self._parent_view.raise_()
		
		