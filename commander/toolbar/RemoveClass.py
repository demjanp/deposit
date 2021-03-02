from deposit.commander.toolbar._Tool import (Tool)

class RemoveClass(Tool):
	
	def name(self):
		
		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ == "ClassVis":
			return "Remove Class"
		else:
			return "Remove Objects from Class"
	
	def icon(self):
		
		return "remove_class.svg"
	
	def help(self):
		
		return self.name()
	
	def enabled(self):
		
		current = self.view.mdiarea.get_current()
		if current:
			for row in current.get_selected():
				for item in row:
					if (item.element.__class__.__name__ == "DObject") or (item.element.__class__.__name__ == "DClass"):
						return True
					return False
		return False
	
	def triggered(self, state):
		
		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ == "QueryLst":
			objects = list(current.get_selected_objects().values())
			if objects:
				self.view.dialogs.open("RemoveObjectsFromClass", objects)
				return
		elif current.__class__.__name__ == "ClassVis":
			classes = []
			for row in current.get_selected():
				for item in row:
					if item.element.__class__.__name__ == "DClass":
						classes.append(item.element.name)
			if classes:
				self.view.dialogs.open("RemoveClass", classes, None)

