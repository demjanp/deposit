from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtCore, QtWidgets, QtGui)

class QueryList(Frame, QtWidgets.QListWidget):
	
	def __init__(self, model, view, parent):
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QListWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_store_changed)
		
		self.itemActivated.connect(self.on_activated)
		self.itemSelectionChanged.connect(self.on_selected)
		
		self.populate()
	
	def get_selected(self):
		
		return [item.text() for item in self.selectedItems()]
	
	def populate(self):
		
		selected = self.get_selected()
		
		self.clear()
		
		data = self.model.queries.to_dict()  # {title: querystr, ...}
		for title in data:
			self.addItem(QtWidgets.QListWidgetItem(title))
		
		if selected:
			for row in range(self.count()):
				item = self.item(row)
				if item.text() in selected:
					item.setSelected(True)
	
	def on_activated(self, item):
		
		self.view.query(self.model.queries.get(item.text()))
	
	def on_selected(self):
		
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_store_changed(self, *args):
		
		self.populate()

