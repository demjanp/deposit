from deposit.commander.toolbar._Tool import (Tool)

class About(Tool):
	
	def name(self):
		
		return "About"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "About Deposit"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		self.view.dialogs.open("About")
