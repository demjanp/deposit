'''
	Main Window View
	--------------------------

	Created on 30. 9. 2017

	@author: Peter Demjan <peter.demjan@gmail.com>
	
'''

from deposit.commander.ClassList import ClassList
from deposit.commander.DatabaseList import DatabaseList
from deposit.commander.QueryComboBox import QueryComboBox
from deposit.commander.MdiArea import MdiArea, MdiSubWindow
from deposit.commander.QueryView import QueryView
from deposit.commander.QueryLstView import QueryLstView
from deposit.commander.QueryImgView import QueryImgView
from deposit.commander.QueryObjView import QueryObjView
from deposit.commander.QueryModel import QueryModel
from deposit.commander.DescriptorView import DescriptorView
from deposit.commander.Descriptor3DView import Descriptor3DView
from deposit.commander.DescriptorModel import DescriptorModel
from deposit.commander.ShapefileView import ShapefileView
from deposit.commander.ShapefileModel import ShapefileModel
from deposit.commander.XLSXWorkbookModel import XLSXWorkbookModel
from deposit.commander.XLSXWorkbookView import XLSXWorkbookView
from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.ExternalLstView import ExternalLstView
from deposit.DLabel import (id_to_name)
from deposit import (Store, DB, File)
from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
from importlib import import_module
from urllib.parse import urlparse
import os
import sys

def signal_handler(func, *args_add):
	
	def func_wrapper(*args):
		return func(*(args_add + args))
	return func_wrapper

class MainWindowView(*uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "MainWindow.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	action = QtCore.pyqtSignal(str, str, tuple) # (signal, name, tuple)
	
	def __init__(self):
		
		self._model = None
		self._windows = [] # to store opened windows so they don't get destroyed
		self._plugins = {} # {name: [action, Model, View, label, icon], ...}
		self._open_plugins = []
		
		super(MainWindowView, self).__init__()
		self.setupUi(self)
		
		self._title = self.windowTitle()
		
		self.classList = ClassList(self)
		self.classesFrame.layout().addWidget(self.classList)
		self.dockWidget.visibilityChanged.connect(self.on_dockWidget_toggled)
		
		self.databaseList = DatabaseList(self)
		self.databasesFrame.layout().addWidget(self.databaseList)
	
	def _set_up_mdi_area(self):
		
		self.mdiArea = MdiArea(self)
		self.centralwidget.layout().addWidget(self.mdiArea)
	
	def _set_up_query_combobox(self):
		
		self.queryComboBox = QueryComboBox()
		self.queryLabel = QtWidgets.QLabel("Query: ")
		self.browseToolBar.insertWidget(self.submitQuery, self.queryLabel)
		self.browseToolBar.insertWidget(self.submitQuery, self.queryComboBox)
		# bind combobox events
		self.queryComboBox.lineEdit().returnPressed.connect(signal_handler(self.on_action, "submitted", "Query", self.queryComboBox.lineEdit()))
		self.submitQuery.triggered.connect(signal_handler(self.on_action, "submitted", "Query", self.queryComboBox.lineEdit()))
	
	def _bind_actions(self):
		# bind MainWindowView actions to definitions in the "view_actions" directory
		
		for item in self.__dict__:
			if item.startswith("action"):
				action = self.__dict__[item]
				if isinstance(action, QtWidgets.QAction):
					for signal in ["changed", "toggled", "triggered"]:
						getattr(action, signal).connect(signal_handler(self.on_action, signal, item[6:]))
					action.hovered.connect(signal_handler(self.on_action_hovered, action))
				elif isinstance(action, QtWidgets.QToolButton) or isinstance(action, QtWidgets.QPushButton):
					action.clicked.connect(signal_handler(self.on_action, "clicked", item[6:]))
	
	def _bind_plugin_actions(self):
		
		plugin_path = os.path.join(os.path.dirname(__file__), "plugins")
		for name in os.listdir(plugin_path):
			if name.startswith("_"):
				continue
			found = True
			path_plugin = os.path.join(plugin_path, name)
			if not os.path.isdir(path_plugin):
				continue
			for suffix in ["model", "view", "info"]:
				if not os.path.isfile(os.path.join(path_plugin, "_%s.py" % suffix)):
					found = False
					break
			if not found:
				continue
			icon = None
			path_ico = os.path.join(path_plugin, "icon.svg")
			if os.path.isfile(path_ico):
				icon = QtGui.QIcon(path_ico)
			label = ""
			try:
				module_info = import_module("deposit.commander.plugins.%s._info" % name)
				module_model = import_module("deposit.commander.plugins.%s._model" % name)
				module_view = import_module("deposit.commander.plugins.%s._view" % name)
				if hasattr(module_info, "label"):
					label = module_info.label
			except:
				print("Plugin import:", name, sys.exc_info())
				label = ""
				continue
			if not icon is None:
				action = QtWidgets.QAction(icon, label, self)
			else:
				action = QtWidgets.QAction(label, self)
			action.setStatusTip(label)
			self.pluginsToolBar.addAction(action)
			action.triggered.connect(signal_handler(self.open_plugin, name))
			self._plugins[name] = [action, module_model.Model, module_view.View, label, icon]
		
		if not self._plugins:
			self.pluginsToolBar.hide()
	
	def update_recent(self):
		
		recent = self._model.recent()
		for action in self.menuData.actions():
			if action.data() == "recent":
				action.setParent(None)
		for params_db, path in recent[::-1]:
			action = QtWidgets.QAction(params_db[0], self)
			action.setData("recent")
			action.triggered.connect(signal_handler(self.on_action, "triggered", "Recent", params_db, path))
			self.menuData.addAction(action)
	
	def connect_store_changed(self):
		
		self._model.store_changed.connect(self.on_store_changed)
		self._model.store_changed.connect(self.classList.on_store_changed)	
		self._model.store_changed.connect(self.databaseList.on_store_changed)	
	
	def set_model(self, model):
		
		self._model = model
		
		self._set_up_mdi_area()
		self._set_up_query_combobox()
		self._bind_actions()
		self._bind_plugin_actions()
		self.update_recent()
		self.update_action_states()
		self.classList.set_model(self._model)
		self.databaseList.set_model(self._model)
		self.connect_store_changed()
	
	def set_status(self, text, timeout = 0):
		
		self.statusBar.showMessage(text, timeout)
	
	def set_title(self, name = None):
		
		if name is None:
			self.setWindowTitle(self._title)
		else:
			self.setWindowTitle("%s - %s" % (name, self._title))
	
	def update_action_states(self):
		
		def _get_action_state(action):
			try:
				module = import_module("deposit.commander.view_actions.%s" % action)
			except:
				try:
					module = import_module("deposit.commander.plugins.%s._info" % action)
				except:
#					print("Action %s could not be loaded." % (action))
					return None, None
			if hasattr(module, "get_state"):
				return getattr(module, "get_state")(self._model, self)
			return None, None
		
		def _set_state(name, action):
			enabled, checked = _get_action_state(name)
			action.blockSignals(True)
			if not enabled is None:
				action.setEnabled(enabled)
			if not checked is None:
				action.setChecked(checked)
			if (enabled is None) and (checked is None):
				action.setEnabled(False)
			action.blockSignals(False)
		
		for item in self.__dict__:
			if item.startswith("action"):
				action = self.__dict__[item]
				_set_state(item[6:], action)
		for name in self._plugins:
			_set_state(name, self._plugins[name][0])
		
		query_enabled = _get_action_state("Query")[0]
		self.submitQuery.setEnabled(query_enabled)
		self.queryComboBox.setEnabled(query_enabled)
		self.queryLabel.setEnabled(query_enabled)
		
		active = self.active()
		if isinstance(active, DescriptorView) or isinstance(active, Descriptor3DView):
			self.descriptorToolBar.show()
		else:
			self.descriptorToolBar.hide()
		
		self.mdiArea.set_object_drag_enabled(query_enabled)
		self.mdiArea.set_class_drag_enabled(query_enabled)
		self.mdiArea.set_trash_enabled(query_enabled)
		
#		self.toolBox.setItemEnabled(1, False) # disable Remote Databases toolbox
	
	def get_query(self, query, relation = None, object_first = None, cls_id = None):
		# TODO factor: self._model.store_changed.connect(view.on_store_changed) to PrototypeList (?)
		
		model = QueryModel(self._model, query, relation, cls_id)
		view = QueryView(self, object_first)
		view.setParent(self)
		model.set_view(view)
		view.set_model(model)
		self._model.store_changed.connect(view.on_store_changed)
		return view
	
	def open_query(self, query, object_first = None, cls_id = None):
		
		self._windows.append(self.get_query(query, object_first = object_first, cls_id = cls_id))
		self.mdiArea.add_window(self._windows[-1])
	
	def open_descriptor(self, obj_id, rel_id):
		# TODO factor: self._model.store_changed.connect(view.on_store_changed) to PrototypeList (?)
		
		model = DescriptorModel(self._model, obj_id, rel_id)
		if model.is_3d():
			view = Descriptor3DView(self)
		else:
			view = DescriptorView(self)
		view.setParent(self)
		model.set_view(view)
		view.set_model(model)
		self._model.store_changed.connect(view.on_store_changed)
		self._windows.append(view)
		self.mdiArea.add_window(self._windows[-1])
	
	def open_resource(self, obj_id, rel_id):
		
		path, filename, storage_type = self._model.store.resources.get_path(self._model.store.get_label(rel_id).label)
		online = (storage_type in [self._model.store.resources.RESOURCE_ONLINE, self._model.store.resources.RESOURCE_CONNECTED_ONLINE])
		self._model.store.file.open(path, filename, online = online)
	
	def open_object(self, obj_id):
		
		if not "#" in obj_id:
			obj_id = id_to_name(obj_id)
		self.open_query("obj(%s).*" % (obj_id), object_first = True)
	
	def open_class(self, cls_id):
		
		if cls_id == "!*":
			query = "!*.* or !*"
			cls_id = None
		elif self._model.store.classes.is_descriptor(cls_id):
			query = "*.%s" % self._model.store.get_label(cls_id).value
			cls_id = None
		else:
			query = "%(cls)s.* or %(cls)s" % dict(cls = self._model.store.get_label(cls_id).value)
		self.open_query(query, cls_id = cls_id)
	
	def open_shapefile(self, uri):
		# TODO factor: self._model.store_changed.connect(view.on_store_changed) to PrototypeList (?)
		
		model = ShapefileModel(self._model, uri)
		view = ShapefileView(self)
		view.setParent(self)
		model.set_view(view)
		view.set_model(model)
		self._model.store_changed.connect(view.on_store_changed)
		self._windows.append(view)
		self.mdiArea.add_window(self._windows[-1])
	
	def open_xlsx(self, uri):
		# TODO factor: self._model.store_changed.connect(view.on_store_changed) to PrototypeList (?)
		
		model = XLSXWorkbookModel(self._model, uri)
		view = XLSXWorkbookView(self)
		view.setParent(self)
		model.set_view(view)
		view.set_model(model)
		self._model.store_changed.connect(view.on_store_changed)
		self._windows.append(view)
		self.mdiArea.add_window(self._windows[-1])
	
	def open_plugin(self, name, *args, **kwargs):
		
		_, Model, View, label, icon = self._plugins[name]
		model = Model(self._model)
		self._open_plugins.append(View(self, **kwargs))
		self._open_plugins[-1].setWindowTitle(label)
		if not icon is None:
			self._open_plugins[-1].setWindowIcon(icon)
		model.set_view(self._open_plugins[-1])
		self._open_plugins[-1].set_model(model)
		self._open_plugins[-1].show()
	
	def get_plugins(self):
		# return {name: label, ...}
		
		return dict([(name, self._plugins[name][3]) for name in self._plugins])
	
	def close_windows(self):
		
		for subwindow in self.mdiArea.subWindowList():
			if isinstance(subwindow, MdiSubWindow):
				subwindow.close()
		self._windows = []
		for plugin in self._open_plugins.copy():
			plugin.close()
	
	def save_store_in_file(self, save_as = False):
		
		ident = self._model.store.identifier()
		ident_old = ident
		scheme = None
		if ident is None:
			scheme = None
		else:
			scheme = urlparse(ident).scheme
		if save_as or (ident is None) or (scheme != "file"):
			path, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption = "Save Database As", filter = "Resource Description Framework (*.rdf)")
			ident = QtCore.QUrl.fromLocalFile(os.path.splitext(path)[0]).toString() + "#"
		else:
			path = urlparse(ident).path.strip("/\\") + ".rdf"
		if path:
			self._model.store.save_to_file(path)
			if ident_old != ident:
				self._model.set_store(Store(DB(ident)))
			else:
				self._model.update_last_changed()
	
	def save_store_in_database(self, save_as = False):
		
		ident, connstr = self._model.store.params()[0]
		path = self._model.store.params()[1]
		ident_old = ident
		if save_as or (ident is None) or (not connstr):
			values = self.get_values("Store in Database", ("ident", ["Identifier:", "http://localhost/deposit/test1#"]), ("connstr", ["Database:", "postgres://archeoforum:1111@127.0.0.1:5432/dep_test"]), ("path", ["Data path:", "C:/Documents/deposit/data_test1"]))
			if values and values["ident"] and values["connstr"] and values["path"]:
				ident, connstr, path = values["ident"], values["connstr"], values["path"]
		if ident and connstr and path:
			self._model.store.store_in_database(ident, connstr, path)
			if ident_old != ident:
				self._model.set_store(Store(DB(ident, connstr), File(path)))
			else:
				self._model.update_last_changed()
	
	def get_values(self, title, *args):
		# get_values(title, (key1, label), (key2, [label, value]), (key3, [label, [value1, value2, ...]]), ...)
		# if value is bool, add checkbox
		# return {key: value, ...}
		
		dialog = QtWidgets.QDialog(self)
		dialog.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		dialog.setMinimumWidth(256)
		dialog.setWindowTitle(title)
		dialog.setModal(True)
		layout = QtWidgets.QVBoxLayout()
		dialog.setLayout(layout)
		button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal)
		button_box.accepted.connect(dialog.accept)
		button_box.rejected.connect(dialog.reject)
		form_layout = QtWidgets.QFormLayout()
		form = QtWidgets.QWidget()
		form.setLayout(form_layout)
		for key, label_value in args:
			if isinstance(label_value, list):
				label, value = label_value
				if isinstance(value, list):
					edit = QtWidgets.QComboBox()
					edit.addItems(value)
					edit.setEditable(True)
				elif isinstance(value, bool):
					edit = QtWidgets.QCheckBox()
					if value:
						edit.setChecked(True)
				else:
					edit = QtWidgets.QLineEdit(value)
			else:
				label = label_value
				edit = QtWidgets.QLineEdit()
			edit.setProperty("key", key)
			form_layout.addRow(label, edit)
		layout.addWidget(form)
		layout.addWidget(button_box)
		dialog.adjustSize()
		if dialog.exec():
			ret = {}
			while form_layout.rowCount():
				widget = form_layout.takeRow(0).fieldItem.widget()
				key = widget.property("key")
				if isinstance(widget, QtWidgets.QLineEdit):
					ret[key] = widget.text()
				elif isinstance(widget, QtWidgets.QCheckBox):
					ret[key] = widget.isChecked()
				else:
					ret[key] = widget.currentText()
			for key in ret:
				if not ret[key]:
					ret[key] = None
			return ret
		else:
			return None
	
	def get_database(self, title = "Database"):
		# get connection details from user
		# return DB, File
		
		values = self.get_values(title, ("ident", ["Identifier:", "http://localhost/deposit/test2#"]), ("connstr", ["Database:", "postgres://archeoforum:1111@127.0.0.1:5432/dep_test"]), ("path", ["Data path:", "C:/Documents/deposit/data_test1"]))
		if values and values["ident"]:
			db = DB(values["ident"], values["connstr"])
			file = File(values["path"]) if values["path"] else None
			return db, file
		return None, None
	
	def active(self):
		# return the active widget or None
		
		valid_classes = [DatabaseList, QueryLstView, QueryImgView, QueryObjView, DescriptorView, ExternalLstView]
		for subwindow in self.mdiArea.subWindowList():
			widget = subwindow.widget()
			if widget is None:
				continue
			active = (widget.__class__ in valid_classes) and widget.hasFocus()
			active_child = None
			for child in widget.findChildren(QtWidgets.QWidget):
				if (child.__class__ in valid_classes) and child.hasFocus():
					if (active_child is None) or (child.hasFocus()):
						active_child = child
			if active_child:
				return active_child
			if active:
				return widget
		if self.classList.hasFocus():
			return self.classList
		return None
	
	def selected(self):
		
		active = self.active()
		if not active is None:
			return active.selected()
		return []
	
	def process_drop(self, source_widget, parent, source_datalist, target_data, event):
		
		if not source_datalist:
			return
		DropAction = source_widget.get_drop_action(parent, source_datalist[0], target_data)
		if not DropAction:
			return
		if self._model.has_store():
			self._model.store.begin_change()
		relation = None
		for source_data in source_datalist:
			action = DropAction(self._model, self, parent, source_data, target_data, event, relation)
			relation = action.relation()
		if self._model.has_store():
			self._model.store.end_change()
	
	def on_subwindow_activated(self, subwindow):
		
		self.update_action_states()
	
	def on_widget_show(self):
		
		self.update_action_states()
	
	def on_widget_focus(self):
		
		self.update_action_states()
	
	def on_action(self, signal, name, *args):
		
		try:
			module = import_module("deposit.commander.view_actions.%s" % name)
		except:
			return
		if hasattr(module, signal):
			getattr(module, signal)(*([self._model, self] + list(args)))
		else:
			self.action.emit(signal, name, args)
	
	def on_action_hovered(self, action):
		
		self.set_status(action.toolTip(), 2000)
	
	def on_showDocklist_toggled(self, checked = None):
		
		if checked:
			self.dockWidget.show()
		else:
			self.dockWidget.close()
	
	def on_dockWidget_toggled(self, *args):
        
		self.showDocklist.setChecked(self.dockWidget.isVisible())
	
	def on_store_changed(self, ids):
		
		self.update_action_states()
		self.update_recent()
		if self._model.has_store():
			if self._model.store.server_url() is None:
				self.set_title("New Database")
				return
			ident = self._model.store.identifier().split("/")[-1].strip("#")
			ident_check = self._model.store.check_out_source()
			if not ident_check is None:
				ident = "%s (Checked Out from %s)" % (ident, ident_check)
			self.set_title(ident)
			return
		self.set_title()
	
	def on_store_message(self, text):
		
		self.set_status(text)
	
	def on_selection_changed(self):
		
		self.update_action_states()
	
	def on_plugin_close(self, plugin):
		
		if plugin in self._open_plugins:
			del self._open_plugins[self._open_plugins.index(plugin)]
	
	def closeEvent(self, event):
		
		if self._model.has_store() and (self._model.last_changed() != self._model.store.get_changed()):
			reply = QtWidgets.QMessageBox.question(self, "Exit", "Save changes to database?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
			if reply == QtWidgets.QMessageBox.Yes:
				if self._model.store.has_database():
					self.save_store_in_database()
				else:
					self.save_store_in_file()
		self.close_windows()
		super(MainWindowView, self).closeEvent(event)
		
