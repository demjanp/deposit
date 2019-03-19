from deposit.commander.usertools._UserElementList import (UserElementList)

class SearchForm(UserElementList):
	
	def __init__(self, label, view):
		
		UserElementList.__init__(self, label, view)
		
		self.setIcon(view.get_icon("search.svg"))
		
	def on_triggered(self, state):
		
		pass
	
