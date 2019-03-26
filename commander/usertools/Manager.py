from deposit import Broadcasts

from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools.EditorForm import (EditorForm)
from deposit.commander.usertools.EditorQuery import (EditorQuery)
from deposit.commander.usertools._UserTool import (UserTool)
from deposit.commander.usertools.SearchForm import (SearchForm)
from deposit.commander.usertools.EntryForm import (EntryForm)
from deposit.commander.usertools.Query import (Query)
from deposit.store.Conversions import (as_path)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class Manager(ViewChild, QtWidgets.QDialog):
	
	def __init__(self, model, view):
		
		ViewChild.__init__(self, model, view)
		QtWidgets.QDialog.__init__(self, view)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.setStyleSheet("QPushButton {Text-align:left;}")
		self.setWindowTitle("User Tool Manager")
		self.setMinimumWidth(300)
		self.setModal(True)
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.tool_list = QtWidgets.QListWidget()
		self.tool_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.controls = QtWidgets.QFrame()
		self.controls.setLayout(QtWidgets.QVBoxLayout())
		self.controls.layout().setContentsMargins(0, 0, 0, 0)
		
		self.button_add_query = QtWidgets.QPushButton("Add Query")
		self.button_add_query.setIcon(self.view.get_icon("add_query.svg"))
		self.button_add_query.setIconSize(QtCore.QSize(32, 32))
		self.button_add_query.clicked.connect(self.on_add_query)
		self.controls.layout().addWidget(self.button_add_query)
		
		self.button_add_search = QtWidgets.QPushButton("Add Search Form")
		self.button_add_search.setIcon(self.view.get_icon("add_search.svg"))
		self.button_add_search.setIconSize(QtCore.QSize(32, 32))
		self.button_add_search.clicked.connect(self.on_add_search)
		self.controls.layout().addWidget(self.button_add_search)
		
		self.button_add_entry = QtWidgets.QPushButton("Add Entry Form")
		self.button_add_entry.setIcon(self.view.get_icon("add_form.svg"))
		self.button_add_entry.setIconSize(QtCore.QSize(32, 32))
		self.button_add_entry.clicked.connect(self.on_add_entry)
		self.controls.layout().addWidget(self.button_add_entry)
		
		self.button_edit = QtWidgets.QPushButton("Edit")
		self.button_edit.setIcon(self.view.get_icon("edit.svg"))
		self.button_edit.setIconSize(QtCore.QSize(32, 32))
		self.button_edit.clicked.connect(self.on_edit)
		self.controls.layout().addWidget(self.button_edit)
		
		self.button_delete = QtWidgets.QPushButton("Delete")
		self.button_delete.setIcon(self.view.get_icon("delete.svg"))
		self.button_delete.setIconSize(QtCore.QSize(32, 32))
		self.button_delete.clicked.connect(self.on_delete)
		self.controls.layout().addWidget(self.button_delete)
		
		self.button_order_up = QtWidgets.QPushButton("Order Up")
		self.button_order_up.setIcon(self.view.get_icon("up_small.svg"))
		self.button_order_up.setIconSize(QtCore.QSize(32, 32))
		self.button_order_up.clicked.connect(self.on_order_up)
		self.controls.layout().addWidget(self.button_order_up)
		
		self.button_order_down = QtWidgets.QPushButton("Order Down")
		self.button_order_down.setIcon(self.view.get_icon("down_small.svg"))
		self.button_order_down.setIconSize(QtCore.QSize(32, 32))
		self.button_order_down.clicked.connect(self.on_order_down)
		self.controls.layout().addWidget(self.button_order_down)
		
		self.button_export = QtWidgets.QPushButton("Export")
		self.button_export.setIcon(self.view.get_icon("export.svg"))
		self.button_export.setIconSize(QtCore.QSize(32, 32))
		self.button_export.clicked.connect(self.on_export)
		self.controls.layout().addWidget(self.button_export)
		
		self.button_import = QtWidgets.QPushButton("Import")
		self.button_import.setIcon(self.view.get_icon("import.svg"))
		self.button_import.setIconSize(QtCore.QSize(32, 32))
		self.button_import.clicked.connect(self.on_import)
		self.controls.layout().addWidget(self.button_import)
		
		self.controls.layout().addStretch()
		
		self.layout().addWidget(self.tool_list)
		self.layout().addWidget(self.controls)
		
		self.populate()
		self.update()
		
		self.tool_list.itemSelectionChanged.connect(self.on_selection_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_data_changed)
		
	def start_query_editor(self, query_tool = None):
		
		self.view.usertools.manager.hide()
		dialog = EditorQuery(self.model, self.view, query_tool)
		dialog.show()
	
	def start_form_editor(self, form_tool = None, entry = False):
		
		self.view.usertools.manager.hide()
		self.view.usertools.form_editor = EditorForm(self.model, self.view, form_tool, entry)
		self.view.usertools.form_editor.show()
	
	def stop_form_editor(self):
		
		self.view.usertools.form_editor.close()
		self.view.usertools.form_editor = None
	
	def populate(self):
		
		self.tool_list.clear()
		for action in self.view.usertools.toolbar.actions():
			if not issubclass(action.__class__, UserTool):
				continue
			item = QtWidgets.QListWidgetItem(action.icon(), action.text())
			item._tool = action
			self.tool_list.addItem(item)
	
	def get_selected(self):
		
		return [item._tool for item in self.tool_list.selectedItems()]
	
	def update(self):
		
		selected = self.get_selected()
		self.button_edit.setEnabled(len(selected) == 1)
		self.button_delete.setEnabled(len(selected) > 0)
		self.button_order_up.setEnabled(len(selected) == 1)
		self.button_order_down.setEnabled(len(selected) == 1)
		self.button_export.setEnabled(len(selected) == 1)
	
	def closeEvent(self, event):
		
		self.disconnect_broadcast()
	
	def on_edit(self, *args):
		
		tool = self.get_selected()[0]
		if isinstance(tool, Query):
			self.start_query_editor(tool)
		if isinstance(tool, SearchForm):
			self.start_form_editor(tool, entry = False)
		elif isinstance(tool, EntryForm):
			self.start_form_editor(tool, entry = True)
	
	def on_add_query(self, *args):
		
		self.start_query_editor()
	
	def on_add_search(self, *args):
		
		self.start_form_editor(entry = False)
	
	def on_add_entry(self, *args):
		
		self.start_form_editor(entry = True)
	
	def on_delete(self, *args):
		
		labels = [tool.label for tool in self.get_selected()]
		reply = QtWidgets.QMessageBox.question(self, "Delete Tool", "Delete %d tools?" % (len(labels)), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		if reply != QtWidgets.QMessageBox.Yes:
			return
		for label in labels:
			self.view.usertools.del_tool(label)
	
	def on_order_up(self, *args):
		
		pass
	
	def on_order_down(self, *args):
		
		pass
	
	def on_export(self, *args):
		
		url, format = QtWidgets.QFileDialog.getSaveFileUrl(self.view, caption = "Export User Tool As", filter = "Text file (*.txt)")
		url = url.toString()
		if not url:
			return
		path = as_path(url, check_if_exists = False)
		if path is None:
			return
		self.view.usertools.export_tool(self.get_selected()[0], path)
	
	def on_import(self, *args):
		
		url, format = QtWidgets.QFileDialog.getOpenFileUrl(self.view, caption = "Import User Tool", filter = "(*.txt)")
		url = url.toString()
		if not url:
			return
		path = as_path(url)
		if path is None:
			return
		self.view.usertools.import_tool(path)
	
	def on_selection_changed(self, *args):
		
		self.update()
	
	def on_data_changed(self, *args):
		
		self.populate()
		self.update()

