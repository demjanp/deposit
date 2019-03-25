from deposit.commander.usertools._UserElementList import (UserElementList)

class SearchForm(UserElementList):
	
	def __init__(self, label, view):
		
		UserElementList.__init__(self, label, view)
		
		self.setIcon(view.get_icon("search.svg"))
		self.setToolTip("Search Form: %s" % self.label)
	
	def on_triggered(self, state):
		
		self.view.usertools.open_search_form(self)
	
