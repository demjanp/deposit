from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.navigator.QueryList import (QueryList)
from deposit.store.Conversions import (as_url)
from deposit.store.Store import (Store)

from PySide2 import (QtWidgets, QtCore, QtGui)

class QueryWidget(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent):
		
		self.layout = None
		self.querylist = None
		self.footer = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.querylist = QueryList(self.model, self.view, self)
		self.layout.addWidget(self.querylist)
		
		self.footer = QueryFooter(self)
		self.layout.addWidget(self.footer)
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		
		self.update_footer()
	
	def get_selected(self):
		
		return self.querylist.get_selected()
	
	def update_footer(self):
		
		selected = self.get_selected()
		
		self.footer.set_edit_enabled(len(selected) > 0)
		self.footer.set_remove_enabled(len(selected) > 0)
	
	def on_view_action(self, args):

		self.update_footer()

	def add_query(self):
		
		querystr = ""
		current = self.view.mdiarea.get_current()
		if hasattr(current, "query"):
			querystr = current.query.querystr
		
		self.view.dialogs.open("AddQuery", querystr)
	
	def edit_query(self):
		
		selected = self.get_selected()
		if not selected:
			return
		self.view.dialogs.open("EditQuery", selected[0], self.model.queries.get(selected[0]))
		
	def remove_query(self):
		
		selected = self.get_selected()
		if not selected:
			return
		reply = QtWidgets.QMessageBox.question(self.view, "Remove Queries", "Remove %d selected Queries?" % (len(selected)), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			for title in selected:
				self.model.queries.delete(title)
	
class QueryFooter(DModule, QtWidgets.QFrame):
	
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
		
		self.button_add_query = QtWidgets.QToolButton(self)
		self.button_add_query.setIcon(self.parent.view.get_icon("add_query.svg"))
		self.button_add_query.setIconSize(QtCore.QSize(32, 32))
		self.button_add_query.setToolTip("Add Query")
		self.button_add_query.clicked.connect(self.on_add_query)
		self.layout.addWidget(self.button_add_query)
		
		self.button_edit_query = QtWidgets.QToolButton(self)
		self.button_edit_query.setIcon(self.parent.view.get_icon("edit_query.svg"))
		self.button_edit_query.setIconSize(QtCore.QSize(32, 32))
		self.button_edit_query.setToolTip("Edit Query")
		self.button_edit_query.clicked.connect(self.on_edit_query)
		self.layout.addWidget(self.button_edit_query)
		
		self.button_remove_query = QtWidgets.QToolButton(self)
		self.button_remove_query.setIcon(self.parent.view.get_icon("remove_query.svg"))
		self.button_remove_query.setIconSize(QtCore.QSize(32, 32))
		self.button_remove_query.setToolTip("Remove Query")
		self.button_remove_query.clicked.connect(self.on_remove_query)
		self.layout.addWidget(self.button_remove_query)
	
	def set_edit_enabled(self, state):
		
		self.button_edit_query.setEnabled(state)
	
	def set_remove_enabled(self, state):
		
		self.button_remove_query.setEnabled(state)
	
	def on_add_query(self, *args):
		
		self.parent.add_query()
	
	def on_edit_query(self, *args):
		
		self.parent.edit_query()
	
	def on_remove_query(self, *args):
		
		self.parent.remove_query()
	
