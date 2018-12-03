from deposit.commander.toolbar._Tool import (Tool)

class RelationName(Tool):
	
	def name(self):
		
		return ""
	
	def combo(self):

		collect = []
		current = self.view.mdiarea.get_current()
		if hasattr(current, "query"):
			for cls in current.query.classes:
				for name in self.model.classes[cls].relations:
					collect.append(name)
		if not collect:
			collect = self.model.relation_names
		collect = [name[1:] if name.startswith("~") else name for name in collect]
		return sorted(list(set(collect)))
	
	def enabled(self):
		
		return True

	