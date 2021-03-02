from deposit.commander.toolbar._Tool import (Tool)

class AddDescriptor(Tool):
	
	def name(self):
		
		return "Add Descriptor"
	
	def icon(self):
		
		return "add_descriptor.svg"
	
	def help(self):
		
		return "Add Descriptor"
	
	def enabled(self):

		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ in ["QueryLst", "QueryObj"]:
			return True
		if current:
			for row in current.get_selected():
				for item in row:
					if (item.element.__class__.__name__ == "DObject") or (item.element.__class__.__name__ == "DClass"):
						return True
					return False
		return False
	
	def triggered(self, state):

		objects = []
		current = self.view.mdiarea.get_current()
		if current.__class__.__name__ == "ClassVis":
			classes = []
			for row in current.get_selected():
				for item in row:
					if item.element.__class__.__name__ == "DClass":
						classes.append(item.element.name)
			if classes:
				self.view.dialogs.open("AddDescriptor", classes)
			return
		elif current:
			for row in current.get_selected():
				for item in row:
					if (item.element.__class__.__name__ == "DObject") and (not item.element in objects):
						objects.append(item.element)
		if objects:
			self.view.dialogs.open("AddDescriptor", objects)
		else:
			classes = [name for name in current.query.classes if name != "!*"]
			if classes:
				self.view.dialogs.open("AddDescriptor", classes)

