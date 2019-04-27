from deposit import Broadcasts

from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.menu._ordering import ordering as MENU_ORDERING
from deposit.commander.menu._ordering import recent as MENU_RECENT
from deposit.commander.toolbar._Toolbar import (Action)

from deposit.commander.menu.ClearLocalFolder import (ClearLocalFolder)
from deposit.commander.menu.ClearRecent import (ClearRecent)
from deposit.commander.menu.Copy import (Copy)
from deposit.commander.menu.SaveAs import (SaveAs)
from deposit.commander.menu.SaveAsDB import (SaveAsDB)
from deposit.commander.menu.SaveAsDBRel import (SaveAsDBRel)
from deposit.commander.menu.SetIdentifier import (SetIdentifier)
from deposit.commander.menu.SetLocalFolder import (SetLocalFolder)
from deposit.commander.menu.SaveHistory import (SaveHistory)
from deposit.commander.menu.History import (History)
from deposit.commander.menu.About import (About)

from PySide2 import (QtWidgets, QtCore, QtGui)
from pathlib import Path
import json
import os

class Menu(CmdDict, ViewChild):
	
	def __init__(self, model, view):
		
		self.menubar = None
		self.actions = {} # {name: Action, ...}
		self.recent_menu = None

		CmdDict.__init__(self, ClearLocalFolder, ClearRecent, Copy, SaveAs, SaveAsDB, SaveAsDBRel, SetIdentifier, SetLocalFolder, SaveHistory, History, About)
		ViewChild.__init__(self, model, view)
		
		self.set_up()
		
	def set_up(self):
		
		self.menubar = self.view.menuBar()
		
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
	
	def load_recent(self):
		
		rows = self.view.registry.get("recent")
		if rows == "":
			return
		rows = json.loads(rows)
		for row in rows:
			if len(row) == 1:
				self.add_recent_url(row[0])
			elif len(row) == 2:
				self.add_recent_db(*row)
	
	def save_recent(self):
		
		rows = []
		for action in self.recent_menu.actions():
			if not isinstance(action, Action):
				continue
			data = action.get_data()
			if isinstance(data, list):
				rows.append(data)
		self.view.registry.set("recent", json.dumps(rows))
	
	def get_recent(self):
		# return [[url], [identifier, connstr], ...]
		
		collect = []
		for action in self.recent_menu.actions():
			if not isinstance(action, Action):
				continue
			data = action.get_data()
			if isinstance(data, list):
				collect.append(data)
		return collect
	
	def clear_recent(self):
		
		for action in self.recent_menu.actions():
			if not isinstance(action, Action):
				continue
			if isinstance(action.get_data(), list):
				action.setParent(None)
	
	def has_recent(self, data):
		
		for action in self.recent_menu.actions():
			if not isinstance(action, Action):
				continue
			if action.get_data() == data:
				return True
		return False
	
	def add_recent_url(self, url):
		
		if self.has_recent([url]):
			return
		action = Action(self, url, "url")
		action.set_data([url])
		self.recent_menu.addAction(action)
		self.save_recent()
	
	def add_recent_db(self, identifier, connstr):

		if self.has_recent([identifier, connstr]):
			return
		name = "%s (%s)" % (identifier, os.path.split(connstr)[1])
		action = Action(self, name, "db")
		action.set_data([identifier, connstr])
		self.recent_menu.addAction(action)
	
	def on_recent_triggered(self, data):
		
		if len(data) == 1:
			url = data[0]
			self.model.load(url)
		elif len(data) == 2:
			identifier, connstr = data
			self.model.load(identifier, connstr)
	
	def on_triggered(self, action):
		
		data = action.get_data()
		if isinstance(data, list):
			self.on_recent_triggered(data)
			return
		self[str(data)].triggered(action.isChecked())
		self.update_tools()
	
	def on_action_hovered(self, action):
		
		self.view.statusbar.message(action.toolTip())
	
	def on_view_action(self, args):

		self.update_tools()

	def on_loaded(self, args):
		
		self.update_tools()
	
