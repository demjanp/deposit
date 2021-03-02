from deposit.commander.toolbar._Tool import (Tool)

class AddClass(Tool):
	
	def name(self):
		
		current = self.view.mdiarea.get_current()
		if (current is None) or (current.__class__.__name__ == "ClassVis"):
			return "Add Class"
		else:
			return "Add Objects to Class"
	
	def icon(self):
		
		return "add_class.svg"
	
	def help(self):
		
		return self.name()
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ == "QueryObj":
			self.view.dialogs.open("AddClass", current.object)
			return
		
		if current.__class__.__name__ == "QueryLst":
			objects = list(current.get_selected_objects().values())
			if objects:
				self.view.dialogs.open("AddClass", objects)
				return
		
		self.view.dialogs.open("AddClass")
		