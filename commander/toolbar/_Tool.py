from deposit.DModule import (DModule)

class Tool(DModule):
	
	def __init__(self, model, view):
		
		self.id = None
		self.model = model
		self.view = view

		DModule.__init__(self)
	
	def combo(self):
		# return a list of values if tool should be a QComboBox
		
		return None
	
	def name(self):
		
		return self.__class__.__name__
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return self.name()
	
	def enabled(self):
		
		return False
	
	def checkable(self):
		
		return False
	
	def checked(self):
		
		return False
	
	def shortcut(self):
		
		return ""
	
	def triggered(self, state):
		
		pass
	