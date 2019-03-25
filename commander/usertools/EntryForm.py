from deposit.commander.usertools._UserElementList import (UserElementList)

class EntryForm(UserElementList):
	
	def __init__(self, label, view):
		
		UserElementList.__init__(self, label, view)
		
		self.setIcon(view.get_icon("form.svg"))
		self.setToolTip("Entry Form: %s" % self.label)
		
	def on_triggered(self, state):
		
		self.view.usertools.open_entry_form(self)
	
