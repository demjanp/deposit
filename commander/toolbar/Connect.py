from deposit import Broadcasts
from deposit.commander.toolbar._Tool import (Tool)

class Connect(Tool):

	def name(self):

		if not self.model.data_source is None:
			return "Disconnect from DB"
		return "Connect to DB"
		
	def icon(self):
		
		if not self.model.data_source is None:
			return "disconnect.svg"
		return "connect.svg"
		
	def help(self):
		
		if not self.model.data_source is None:
			return "Disconnect from Database"
		return "Connect to Database"
		
	def enabled(self):

		return True
		
	def checkable(self):

		return True
		
	def checked(self):

		return (not self.model.data_source is None)
		
	def triggered(self, state):
		
		if not self.model.data_source is None:
			self.model.set_datasource(None)
			self.broadcast(Broadcasts.VIEW_ACTION)
		else:
			self.view.dialogs.open("Connect")
