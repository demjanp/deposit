from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_url)

from PySide2 import (QtWidgets, QtCore, QtGui)

from pathlib import Path
import os

class OpenJSON(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		homedir = self.view.registry.get("recent_dir")
		if not homedir:
			homedir = str(Path.home())
		self.fs_model = QtWidgets.QFileSystemModel()
		self.fs_model.setRootPath(homedir)
		self.fs_model.setNameFilters(["*.json"])
		self.fs_model.setNameFilterDisables(False)
		self.tree = FileTree()
		self.tree.setModel(self.fs_model)
		for i in range(1, self.fs_model.columnCount()):
			self.tree.hideColumn(i)
		self.tree.setCurrentIndex(self.fs_model.index(homedir))
		self.tree.setExpanded(self.fs_model.index(homedir), True)
		self.tree.setAnimated(False)
		self.tree.setIndentation(20)
		self.tree.setSortingEnabled(True)
		self.tree.selected.connect(self.on_selected)
		
		self.path_edit = QtWidgets.QLineEdit()
		self.path_edit.textChanged.connect(self.on_path_changed)
		
		self.connect_button = QtWidgets.QPushButton("Connect")
		self.connect_button.clicked.connect(self.on_connect)
		
		self.layout().addWidget(self.tree)
		self.layout().addWidget(self.path_edit)
		self.layout().addWidget(self.connect_button)
		
		self.update()
	
	def get_path(self):
		
		path = self.path_edit.text().strip()
		if (not path) or os.path.isdir(path):
			return ""
		path, filename = os.path.split(path)
		filename, ext = os.path.splitext(filename)
		if ext.lower() != ".json":
			ext = ".json"
		path = os.path.join(path, "%s%s" % (filename, ext))
		return path
	
	def update(self):
		
		path = self.get_path()
		if os.path.isfile(path):
			self.connect_button.setText("Connect")
		else:
			self.connect_button.setText("Create")
		self.connect_button.setEnabled(path != "")
	
	def on_selected(self):
		
		index = self.tree.currentIndex()
		path = self.fs_model.filePath(index)
		self.path_edit.setText(path)
	
	def on_path_changed(self):
		
		self.update()
	
	def on_connect(self):
		
		path = self.get_path()
		if not path:
			return
		
		self.view.registry.set("recent_dir", os.path.split(path)[0])
		
		url = as_url(path)
		self.model.load(url)
		
		self.parent.close()

class FileTree(QtWidgets.QTreeView):
	
	selected = QtCore.Signal()
	
	def selectionChanged(self, selected, deselected):
		
		self.selected.emit()
		
		QtWidgets.QTreeView.selectionChanged(self, selected, deselected)

