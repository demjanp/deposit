from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.navigator.DatabaseList import (DatabaseList)
from deposit.store.Conversions import (as_url)
from deposit.store.Store import (Store)

from PySide2 import (QtWidgets, QtCore, QtGui)

class DatabaseWidget(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent):
		
		self.layout = None
		self.databaselist = None
		self.footer = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.databaselist = DatabaseList(self.model, self.view, self)
		self.layout.addWidget(self.databaselist)
		
		self.footer = DatabaseFooter(self)
		self.layout.addWidget(self.footer)
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		
		self.update_footer()
	
	def get_selected(self):
		
		return self.databaselist.get_selected()
	
	def update_footer(self):
		
		selected = self.get_selected()
		
		self.footer.set_merge_enabled(len(selected) > 0)
		self.footer.set_unlink_enabled(len(selected) > 0)
	
	def on_view_action(self, args):

		self.update_footer()

	def link_db(self):
		
		self.view.dialogs.open("LinkDB")
	
	def link_file(self):
		
		pass
		
	def merge(self):
		
		self.model.merge_linked()
	
	def unlink(self):
		
		pass
	
class DatabaseFooter(DModule, QtWidgets.QFrame):
	
	def __init__(self, parent):

		self.parent = parent

		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self)

		self.set_up()

	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(6)
		self.setLayout(self.layout)
		
		self.layout.addStretch()
		
		self.button_link_db = QtWidgets.QToolButton(self)
		self.button_link_db.setIcon(self.parent.view.get_icon("link_db.svg"))
		self.button_link_db.setIconSize(QtCore.QSize(32, 32))
		self.button_link_db.setToolTip("Link Database")
		self.button_link_db.clicked.connect(self.on_link_db)
		self.layout.addWidget(self.button_link_db)
		
		self.button_link_file = QtWidgets.QToolButton(self)
		self.button_link_file.setIcon(self.parent.view.get_icon("link_file.svg"))
		self.button_link_file.setIconSize(QtCore.QSize(32, 32))
		self.button_link_file.setToolTip("Link File")
		self.button_link_db.clicked.connect(self.on_link_file)
		self.layout.addWidget(self.button_link_file)
		
		self.button_merge = QtWidgets.QToolButton(self)
		self.button_merge.setIcon(self.parent.view.get_icon("merge_linked.svg"))
		self.button_merge.setIconSize(QtCore.QSize(32, 32))
		self.button_merge.setToolTip("Merge Linked Database")
		self.button_merge.clicked.connect(self.on_merge)
		self.layout.addWidget(self.button_merge)
		
		self.button_unlink = QtWidgets.QToolButton(self)
		self.button_unlink.setIcon(self.parent.view.get_icon("unlink.svg"))
		self.button_unlink.setIconSize(QtCore.QSize(32, 32))
		self.button_unlink.setToolTip("Unlink Database")
		self.button_unlink.clicked.connect(self.on_unlink)
		self.layout.addWidget(self.button_unlink)
	
	def set_merge_enabled(self, state):
		
		self.button_merge.setEnabled(state)
	
	def set_unlink_enabled(self, state):
		
		self.button_unlink.setEnabled(state)
	
	def on_link_db(self, *args):
		
		self.parent.link_db()
	
	def on_link_file(self, *args):
		
		self.parent.link_file()
	
	def on_merge(self, *args):
		
		self.parent.merge()
	
	def on_unlink(self, *args):
		
		self.parent.unlink()
