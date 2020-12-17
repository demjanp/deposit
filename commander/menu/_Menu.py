from deposit import Broadcasts

from deposit.commander.menu._MRUDMenu import (MRUDMenu)
from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.menu._ordering import ordering as MENU_ORDERING
from deposit.commander.menu._ordering import recent as MENU_RECENT
from deposit.commander.toolbar._Toolbar import (Action)

from deposit.commander.menu.ClearLocalFolder import (ClearLocalFolder)
from deposit.commander.menu.ClearRecent import (ClearRecent)
from deposit.commander.menu.Copy import (Copy)
from deposit.commander.menu.Paste import (Paste)
from deposit.commander.menu.SetLocalFolder import (SetLocalFolder)
from deposit.commander.menu.LocaliseResources import (LocaliseResources)
from deposit.commander.menu.SaveHistory import (SaveHistory)
from deposit.commander.menu.History import (History)
from deposit.commander.menu.About import (About)

from PySide2 import (QtWidgets, QtCore, QtGui)
from pathlib import Path
import json
import os

class Menu(CmdDict, MRUDMenu):
	
	def __init__(self, model, view):
		
		self.menubar = None
		self.actions = {} # {name: Action, ...}
		
		CmdDict.__init__(self, ClearLocalFolder, ClearRecent, Copy, Paste, SetLocalFolder, LocaliseResources, SaveHistory, History, About)
		MRUDMenu.__init__(self, model, view)
		
	def set_up(self):
		
		self.menubar = self.view.tool_window.menuBar()  # DEBUG
		
		menus = {} # {name: QMenu, ...}
		
		for i, row in enumerate(MENU_ORDERING):
			if not row[0] in menus:
				menus[row[0]] = self.menubar.addMenu(row[0])
			for name in row[1:]:
				if name in self.classes:
					self[name] = self.classes[name](self.model, self.view)
				elif name in self.view.toolbar.classes:
					self[name] = self.view.toolbar.classes[name](self.model, self.view)
				else:
					continue
				self.actions[name] = Action(self, self[name].name(), name)
				menus[row[0]].addAction(self.actions[name])
			if (i < len(MENU_ORDERING) - 1) and (MENU_ORDERING[i + 1][0] == row[0]):
				menus[row[0]].addSeparator()
		
		self.recent_menu = menus[MENU_RECENT]
		self.recent_menu.addSeparator()
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		
		self.update_tools()
	
	def update_tools(self):
		
		for name in self:
			tool_name = self[name].name()
			icon = self[name].icon()
			help = self[name].help()
			checkable = self[name].checkable()
			shortcut = self[name].shortcut()
			self.actions[name].setText(tool_name)
			if icon:
				icon = self.view.get_icon(icon)
				self.actions[name].setIcon(icon)
			if shortcut:
				self.actions[name].setShortcut(QtGui.QKeySequence(shortcut))
			self.actions[name].setCheckable(checkable)
			self.actions[name].setToolTip(help)
			self.actions[name].setChecked(self[name].checked())
			self.actions[name].setEnabled(self[name].enabled())
	
	def on_triggered(self, action):
		
		if self.check_recent_triggered(action):
			return
		self[str(action.get_data())].triggered(action.isChecked())
		self.update_tools()
	
	def on_action_hovered(self, action):
		
		self.view.statusbar.message(action.toolTip())
	
	def on_view_action(self, args):

		self.update_tools()

	def on_loaded(self, args):
		
		self.update_tools()
	
