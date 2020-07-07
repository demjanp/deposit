from deposit.commander.toolbar._Tool import (Tool)

class Connect(Tool):
	
	def name(self):
		
		return "Connect Data Source"
	
	def icon(self):
		
		return "connect.svg"
	
	def help(self):
		
		return "Connect to Data Source"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		self.view.dialogs.open("Connect")

