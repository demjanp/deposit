from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_path)

from PySide2 import (QtWidgets, QtCore, QtGui)

import os

class DataSourceRecent(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		self.left = QtWidgets.QFrame()
		self.left.setLayout(QtWidgets.QVBoxLayout())
		self.left.layout().setContentsMargins(0, 0, 0, 0)
		self.right = QtWidgets.QFrame()
		self.right.setLayout(QtWidgets.QVBoxLayout())
		self.right.layout().setContentsMargins(0, 0, 0, 0)
		
		self.recent_list = QtWidgets.QListWidget()
		for row in self.view.menu.get_recent(): # [[url], [identifier, connstr], ...]
			name = None
			if len(row) == 1:
				url = row[0]
				name = url
			elif len(row) == 2:
				identifier, connstr = row
				name = "%s (%s)" % (identifier, os.path.split(connstr)[1])
			if not name:
				continue
			item = QtWidgets.QListWidgetItem(name)
			item.setData(QtCore.Qt.UserRole, row)
			self.recent_list.addItem(item)
		self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.recent_list.itemSelectionChanged.connect(self.on_selected)
		self.recent_list.activated.connect(self.on_connect)
		
		self.connect_button = QtWidgets.QPushButton(self.parent.connect_caption())
		self.connect_button.clicked.connect(self.on_connect)
		
		self.left.layout().addWidget(self.recent_list)
		self.left.layout().addWidget(self.connect_button)
		self.right.layout().addWidget(self.parent.logo())
		self.layout().addWidget(self.left)
		self.layout().addWidget(self.right)
		
		self.update()
	
	def update(self):
		
		self.connect_button.setEnabled(len(self.recent_list.selectedItems()) > 0)
	
	def on_selected(self):
		
		self.update()
	
	def on_connect(self):
		
		item = self.recent_list.currentItem()
		if not item:
			return
		row = item.data(QtCore.Qt.UserRole)
		if len(row) == 1:
			url = row[0]
			path = as_path(url)
			if path is not None:
				self.view.registry.set("recent_dir", os.path.split(path)[0])
				self.parent.on_connect(url, None)
			
		elif len(row) == 2:
			identifier, connstr = row
			self.parent.on_connect(identifier, connstr)

