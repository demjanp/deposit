from deposit.commander.toolbar._Tool import (Tool)

class History(Tool):
	
	def name(self):
		
		return "History"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Event History"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		# DEBUG start
		for t, user, delement, key, func_name, args in self.model.events.to_list():
			print(t, user, delement, key, func_name, args)
		# DEBUG end
		