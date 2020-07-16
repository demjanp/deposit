from deposit import Broadcasts
from deposit.store.Store import (Store)
from deposit.commander.SaveWorker import (SaveWorker)

from PySide2 import (QtCore)
import time

class Model(Store, QtCore.QObject):
	
	save_caller = QtCore.Signal(object)  # data
	
	def __init__(self, parent, *args):
		
		Store.__init__(self, *args, parent = parent)
		QtCore.QObject.__init__(self)
		
		self.set_up()
	
	def set_up(self):
		
		self.save_worker = SaveWorker()
		self.save_thread = QtCore.QThread()
		self.save_worker.moveToThread(self.save_thread)
		self.save_worker.signal_saved.connect(self.on_worker_saved)
		self.save_caller.connect(self.save_worker.save)
		self.save_thread.start()
		self._last_changed = -1
		self._is_saving = False
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)
	
	def save_store(self):
		
		result = Store.save(self)
		if result:
			self.broadcast(Broadcasts.STORE_SAVED)
		else:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
		return result
	
	def save(self):
		
		self._is_saving = True
		data = self.data_source.to_dict()
		self.save_caller.emit(data)
	
	@QtCore.Slot(bool)
	def on_worker_saved(self, result):
		
		self._is_saving = False
		if result:
			self.broadcast(Broadcasts.STORE_SAVED)
		else:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
	
	def is_saved(self):

		return self._last_changed == self.changed

	def on_loaded(self, *args):

		self._last_changed = self.changed
	
	def on_saved(self, *args):

		self._last_changed = self.changed

	def on_close(self):
		
		t0 = time.time()
		while self._is_saving:
			print("Saving...")
			time.sleep(2)
			if time.time() - t0 > 15:
				print("Saving timed out. Data was not saved!")
				break
		self.save_thread.quit()
		self.save_thread.wait(1000)
	
