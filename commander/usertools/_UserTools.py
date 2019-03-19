from deposit import Broadcasts

from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools._Manager import (Manager)
from deposit.commander.usertools.SearchForm import (SearchForm)
from deposit.commander.usertools.EntryForm import (EntryForm)
from deposit.commander.usertools.Query import (Query)
from deposit.commander.usertools import (UserControls)
from deposit.commander.usertools import (UserGroups)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class UserTools(ViewChild):
	
	def __init__(self, model, view):
		
		self.toolbar = None
		self.action_manage = None
		self.edit_toolbar = None
		self.actions = {} # {name: QAction, ...}
		self.manager = None
		self.form_editor = None
		
		ViewChild.__init__(self, model, view)
		
		self.set_up()
		
	def set_up(self):
		
		self.view.addToolBarBreak()
		self.toolbar = self.view.addToolBar("User Tools")
		self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		
		self.action_manage = QtWidgets.QAction("Manage", self.view)
		self.action_manage.triggered.connect(self.on_manage)
		
		self.update_tools()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_data_changed)
	
	def add_tool(self, user_tool):
		
		self.model.user_tools.add(user_tool.to_dict())
	
	def update_tool(self, label, user_tool):
		
		self.model.user_tools.delete(label)
		self.model.user_tools.add(user_tool.to_dict())
	
	def del_tool(self, label):
		
		self.model.user_tools.delete(label)
	
	def user_tool_from_dict(self, data):
		
		user_tool = None
		if data["typ"] == "Query":
			return Query(data["label"], data["value"], self.view)
		else:
			typ = None
			if data["typ"] == "SearchForm":
				typ = SearchForm
			elif data["typ"] == "EntryForm":
				typ = EntryForm
			if typ is not None:
				user_tool = typ(data["label"], self.view)
				if typ in [SearchForm, EntryForm]:
					for element in data["elements"]:
						if element["typ"] in ["Group", "MultiGroup"]:
							user_tool.elements.append(getattr(UserGroups, element["typ"])(element["stylesheet"], element["label"]))
							for member in element["members"]:
								user_tool.elements[-1].members.append(getattr(UserControls, member["typ"])(member["stylesheet"], member["label"], member["dclass"], member["descriptor"]))
						elif element["typ"] == "ColumnBreak":
							pass  # TODO
						else:
							user_tool.elements.append(getattr(UserControls, element["typ"])(element["stylesheet"], element["label"], element["dclass"], element["descriptor"]))
				return user_tool
		return None
	
	def update_tools(self):
		
		self.toolbar.clear()
		self.toolbar.addAction(self.action_manage)
		self.toolbar.addSeparator()
		for data in self.model.user_tools.to_list():
			user_tool = self.user_tool_from_dict(data)
			if user_tool is not None:
				self.toolbar.addAction(user_tool)
	
	def start_manager(self):
		
		self.manager = Manager(self.model, self.view)
		self.manager.show()
	
	def on_manage(self, *args):
		
		self.start_manager()
	
	def on_loaded(self, *args):
		
		self.update_tools()
	
	def on_data_changed(self, *args):
		
		self.update_tools()
	
	def on_close(self):
		
		if self.form_editor is not None:
			self.form_editor.close()

