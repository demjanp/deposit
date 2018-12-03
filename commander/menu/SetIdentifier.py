from deposit.commander.toolbar._Tool import (Tool)

class SetIdentifier(Tool):
	
	def name(self):
		
		return "Set Identifier"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Set Identifier"
	
	def enabled(self):
		
		return (not self.model.data_source is None)
	
	def triggered(self, state):
		
		self.view.dialogs.open("SetIdentifier")
		
		