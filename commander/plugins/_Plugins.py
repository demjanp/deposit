import deposit
from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.plugins._ordering import (ordering)

from deposit.commander.plugins.C14Form import (C14Form)
from deposit.commander.plugins.C14Search import (C14Search)

from PyQt5 import (QtWidgets, QtCore, QtGui)
import os

class Plugins(DModule, CmdDict):
	
	def __init__(self, model, view):
		
		self.model = model
		self.view = view
		self.toolbar = None
		self.actions = {} # {name: QAction, ...}

		DModule.__init__(self)
		CmdDict.__init__(self, C14Form, C14Search)
		
		self.set_up()
	
	def set_up(self):
		
		self.toolbar = self.view.addToolBar("Plugins")
		
		found = []
		for row in ordering:
			for name in row:
				if name in self.classes:
					found.append(name)
		not_found = []
		for name in self.classes:
			if not name in found:
				not_found.append(name)
		if not_found:
			ordering.append(not_found)
		
		for i, row in enumerate(ordering):
			for name in row:
				if name in self.classes:
					self[name] = self.classes[name](self)
					self.actions[name] = QtWidgets.QAction(self[name].name(), self.view)
					self.actions[name].setData(name)
					self.toolbar.addAction(self.actions[name])
					self.actions[name].hovered.connect(self.on_action_hovered)
			if i < len(ordering) - 1:
				self.toolbar.addSeparator()
		
		self.toolbar.actionTriggered.connect(self.on_triggered)
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		
		self.update_tools()
	
	def get_plugin_icon(self, name):
		
		path = os.path.join(os.path.dirname(deposit.__file__), "res", "plugin_icons")
		for ext in self.model.images.IMAGE_EXTENSIONS:
			for ext2 in [ext, ext.upper()]:
				icon_path = os.path.join(path, "%s.%s" % (name, ext2))
				if os.path.isfile(icon_path):
					return QtGui.QIcon(icon_path)
	
	def update_tools(self):

		for name in self:
			self.actions[name].setText(self[name].name())
			self.actions[name].setCheckable(self[name].checkable())
			self.actions[name].setChecked(self[name].active())
			self.actions[name].setToolTip(self[name].help())
			self.actions[name].setEnabled(self[name].enabled())
			icon = self.get_plugin_icon(name)
			if not icon is None:
				self.actions[name].setIcon(icon)
	
	def close_all(self):
		
		for name in self:
			self[name].close()
	
	def on_triggered(self, action):
		
		if action.isChecked() or (not action.isCheckable()):
			self[str(action.data())].activate()
		else:
			self[str(action.data())].close()
		self.update_tools()
	
	def on_action_hovered(self):

		self.view.statusbar.message(self.view.sender().toolTip())
	
	def on_view_action(self, args):

		self.update_tools()
	
	def on_loaded(self, args):

		self.update_tools()
	