from deposit.commander.toolbar._Tool import (Tool)

class AddClass(Tool):
	
	def name(self):
		
		return "Add Objects to Class"
	
	def icon(self):
		
		return "add_class.svg"
	
	def help(self):
		
		return "Add Objects to Class"
	
	def enabled(self):
		
		current = self.view.mdiarea.get_current()
		if current:
			for row in current.get_selected():
				for item in row:
					if item.element.__class__.__name__ == "DObject":
						return True
					return False
		return False
	
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
		

		