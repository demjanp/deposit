from deposit import Broadcasts
from deposit.DModule import (DModule)

class Plugin(DModule):
	
	def __init__(self, parent):
		
		self.parent = parent
		self._active = False

		DModule.__init__(self)

		self.set_up()
	
	def activate(self):
		
		self._active = True
		self.on_activate()
	
	def close(self):
		
		self._active = False
		self.on_close()
	
	def active(self):
		
		return self._active
	
	def set_active(self, state):
		
		self._active = state
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def name(self):
		# re-implement
		
		return self.__class__.__name__
	
	def help(self):
		# re-implement
		
		return self.name()
	
	def enabled(self):
		# re-implement
		
		return False
	
	def checkable(self):
		# re-implement
		
		return False
	
	def set_up(self):
		# re-implement
		
		pass
	
	def on_activate(self):
		# re-implement
		
		pass
	
	def on_close(self):
		# re-implement
		
		pass
	
	
	