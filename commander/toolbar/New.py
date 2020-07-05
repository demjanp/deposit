from deposit.commander.toolbar._Tool import (Tool)

class New(Tool):
	
	def name(self):
		
		return self.__class__.__name__
	
	def icon(self):
		
		return "new_file.svg"
	
	def help(self):
		
		return "New Database"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		self.view.dialogs.open("Open")

