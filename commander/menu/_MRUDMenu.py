from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.toolbar._Toolbar import (Action)

import json
import os

class MRUDMenu(ViewChild):
	
	def __init__(self, model, view):
		
		self.recent_menu = None

		ViewChild.__init__(self, model, view)
		
		self.set_up()
		self.load_recent()
		
	def set_up(self):
		
		# define self.recent_menu here
		pass
	
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
		self.save_recent()
	
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
		if (not identifier) or (not connstr):
			return
		name = "%s (%s)" % (identifier, os.path.split(connstr)[1])
		action = Action(self, name, "db")
		action.set_data([identifier, connstr])
		self.recent_menu.addAction(action)
		self.save_recent()
	
	def check_recent_triggered(self, action):
		
		if not isinstance(action, Action):
			return False
		data = action.get_data()
		if isinstance(data, list):
			if len(data) == 1:
				url = data[0]
				self.model.load(url)
				return True
			elif len(data) == 2:
				identifier, connstr = data
				self.model.load(identifier, connstr)
				return True
		return False

