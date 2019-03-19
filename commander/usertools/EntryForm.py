from deposit.commander.usertools._UserElementList import (UserElementList)

class EntryForm(UserElementList):
	
	def __init__(self, label, view):
		
		UserElementList.__init__(self, label, view)
		
		self.setIcon(view.get_icon("form.svg"))
		
	def on_triggered(self, state):
		
		pass
	
