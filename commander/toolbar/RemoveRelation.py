from deposit.commander.toolbar._Tool import (Tool)

class RemoveRelation(Tool):
	
	def name(self):
		
		return "Remove Relation"
	
	def icon(self):
		
		return "unlink.svg"
	
	def help(self):
		
		return "Remove Relation"
	
	def enabled(self):

		current = self.view.mdiarea.get_current()
		if current:
			for row in current.get_selected():
				for item in row:
					if item.relation is None:
						return False
					else:
						return True
		return False
	
	def triggered(self, state):
		
		items = []
		current = self.view.mdiarea.get_current()
		for row in current.get_selected():
			for item in row:
				if not item.relation is None:
					items.append(item)
		self.view.dialogs.open("RemoveRelation", items)

