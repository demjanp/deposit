from deposit.commander.toolbar._Tool import (Tool)

class ClearLocalFolder(Tool):
	
	def name(self):
		
		return "Clear Local Folder"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Clear Local Folder"
	
	def enabled(self):
		
		return (self.model.local_folder is not None) and (self.model.data_source is not None) and (self.model.data_source.name not in ["JSON", "Pickle"])
	
	def triggered(self, state):
		
		self.model.set_local_folder(None)
		
		