from deposit.commander.toolbar._Tool import (Tool)

class ClassVis(Tool):
	
	def name(self):
		
		return "Class Relations"
	
	def icon(self):
		
		return "classes_graph.svg"
	
	def help(self):
		
		return "Show Class Relations"
	
	def enabled(self):

		return True
	
	def triggered(self, state):
		
		self.view.mdiarea.create("ClassVis")
