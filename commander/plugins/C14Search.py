from deposit.commander.plugins._Plugin import (Plugin)
from deposit.commander.plugins.C14SearchMembers.View import (View)

class C14Search(Plugin):
	
	def name(self):
		
		return "14C Database Search"
	
	def set_up(self):

		self.view = View(self)

	def enabled(self):
		# re-implement
		
		return True
	
	def on_activate(self):

		if not self.view.isVisible():
			self.view.show()
		self.view.on_activate()
	
	def on_close(self):

		if self.view.isVisible():
			self.view.hide()
