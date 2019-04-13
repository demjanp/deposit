from deposit.commander.toolbar._Tool import (Tool)
from PySide2 import (QtWidgets)
import os

class SaveHistory(Tool):
	
	def name(self):
		
		return "Save History"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Save Event History"
	
	def enabled(self):
		
		return True
	
	def checkable(self):

		return True
		
	def checked(self):

		return self.model.save_events
		
	def triggered(self, state):
		
		self.model.set_save_events(state)

