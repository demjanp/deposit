from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.DropActions import DropActions
from PyQt5 import (QtCore, QtWidgets, QtGui)
import os
from urllib.parse import urlparse

class DatabaseList(PrototypeList, QtWidgets.QListWidget):
	
	def __init__(self, parent_view):
		
		super(DatabaseList, self).__init__(parent_view)
		
		self.itemActivated.connect(self.on_activated)
		self.itemSelectionChanged.connect(self.on_selection_changed)
		
		self.setAcceptDrops(True)
		
	def _populate(self):
		
		self.clear()
		if self._model.has_store():
			for identifier in self._model.store.remote_identifiers():
				item = QtWidgets.QListWidgetItem()
				item.setData(QtCore.Qt.DisplayRole, identifier)
				item.setFlags(QtCore.Qt.ItemIsEnabled)
				self.addItem(item)
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if self._model.has_store():
			if src_parent == "external":
				scheme = urlparse(src_data["value"]).scheme
				if (scheme in ["http", "https"]) or (os.path.splitext(src_data["value"])[1].lower() == ".rdf"):
					return DropActions.OPEN_REMOTE
		return None
	
	def selected(self):
		
		return [item.data(QtCore.Qt.UserRole) for item in self.selectedItems()]
	
	def on_set_model(self):
		
		self._populate()
	
	def on_store_changed(self, ids):
		
		self._populate()
	
	def on_activated(self, item):
		
		pass
	
		
