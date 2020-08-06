from deposit import Broadcasts
from deposit.store.Store import (Store)

from PySide2 import (QtCore)
import time

class Model(Store, QtCore.QObject):
	
	def __init__(self, parent, *args):
		
		Store.__init__(self, *args, parent = parent)
		QtCore.QObject.__init__(self)
		
		self.set_up()
	
	def set_up(self):
		
		self._last_changed = -1
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)
	
	def save(self):
		
		result = Store.save(self)
		if result:
			self.broadcast(Broadcasts.STORE_SAVED)
		else:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
		return result
	
	def is_saved(self):

		return self._last_changed == self.changed

	def on_loaded(self, *args):

		self._last_changed = self.changed
	
	def on_saved(self, *args):

		self._last_changed = self.changed

	def on_close(self):
		
		pass
	
