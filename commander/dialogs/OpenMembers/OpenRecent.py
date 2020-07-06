from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_path)

from PySide2 import (QtWidgets, QtCore, QtGui)

import os

class OpenRecent(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		
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
		
		self.connect_button = QtWidgets.QPushButton("Connect")
		self.connect_button.clicked.connect(self.on_connect)
		
		self.layout().addWidget(self.recent_list)
		self.layout().addWidget(self.connect_button)
		
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
			self.view.registry.set("recent_dir", os.path.split(as_path(url))[0])
			self.model.load(url)
			
		elif len(row) == 2:
			identifier, connstr = row
			self.model.load(identifier, connstr)
		
		self.parent.close()

