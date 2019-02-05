from deposit.commander.toolbar._Tool import (Tool)

class ClearLocalFolder(Tool):
	
	def name(self):
		
		return "Clear Local Folder"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Clear Local Folder"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		self.model.set_local_folder(None)
		
		