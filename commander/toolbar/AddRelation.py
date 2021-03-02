from deposit.commander.toolbar._Tool import (Tool)

class AddRelation(Tool):
	
	def name(self):
		
		return "Add Relation"
	
	def icon(self):
		
		return "link.svg"
	
	def help(self):
		
		return "Add Relation"
	
	def enabled(self):

		if self.view.dialogs:
			if self.view.dialogs.is_open("AddRelation"):
				return False
		
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
				self.view.dialogs.open("AddRelation", [self.model.classes[name] for name in classes])
			return
		elif current:
			if current.__class__.__name__ == "QueryObj":
				objects = [current.object]
			else:
				for row in current.get_selected():
					for item in row:
						if (item.element.__class__.__name__ == "DObject") and (not item.element in objects):
							objects.append(item.element)
		
		if objects:
			self.view.dialogs.open("AddRelation", objects)
		else:
			classes = [self.model.classes[name] for name in current.query.classes if name != "!*"]
			if classes:
				self.view.dialogs.open("AddRelation", classes)

