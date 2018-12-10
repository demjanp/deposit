from deposit import Broadcasts
from deposit import (Store)

from PyQt5 import (QtCore)
import os

class Model(Store):
	
	def __init__(self, parent):
		
		Store.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.save_thread = SaveThread(self)
		self._last_changed = -1
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)

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
		
		if not self.model.data_source is None:
			self.model.data_source.save()
