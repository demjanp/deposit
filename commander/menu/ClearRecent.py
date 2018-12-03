from deposit.commander.toolbar._Tool import (Tool)

class ClearRecent(Tool):
	
	def name(self):
		
		return "Clear Recent"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Clear Recent"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		self.view.menu.clear_recent()
		