from deposit.commander.toolbar._Tool import (Tool)

class RemoveObject(Tool):
	
	def name(self):
		
		return "Remove Object"
	
	def icon(self):
		
		return "remove_object.svg"
	
	def help(self):
		
		return "Remove Object"
	
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
		if current:
			objects = list(current.get_selected_objects().values())
			if objects:
				self.view.dialogs.open("RemoveObject", objects)

