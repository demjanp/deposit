from deposit.commander.toolbar._Tool import (Tool)

class AddObject(Tool):
	
	def name(self):
		
		return "Add Object"
	
	def icon(self):
		
		return "add_object.svg"
	
	def help(self):
		
		return "Add Object"
	
	def enabled(self):

		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ == "QueryLst":
			if (len(current.query.parse.selects[0].classes) == 1):
				return True
		return False
	
	def triggered(self, state):
		
		current = self.view.mdiarea.get_current()
		cls = current.query.parse.selects[0].classes[0]
		if cls == "!*":
			self.model.objects.add()
		else:
			self.model.classes[cls].objects.add()
		
		