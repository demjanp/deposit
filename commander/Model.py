from deposit import Broadcasts
from deposit import (Store)

from PySide2 import (QtCore)

class Model(Store):
	
	def __init__(self, parent, *args):
		
		Store.__init__(self, *args, parent = parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.save_thread = SaveThread(self)
		self._last_changed = -1
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)

	def save_store(self):
		
		Store.save(self)
	
	def save(self):

		self.save_thread.wait()
		self.save_thread.start()

	def is_saved(self):

		return self._last_changed == self.changed

	def on_loaded(self, *args):

		self._last_changed = self.changed

	def on_saved(self, *args):

		self._last_changed = self.changed

	def on_close(self):
		
		self.save_thread.wait()
	
class SaveThread(QtCore.QThread):
	
	def __init__(self, model):
		
		self.model = model
		
		QtCore.QThread.__init__(self)
	
	def run(self):
		
		self.model.save_store()
