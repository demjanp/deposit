from deposit import (Store)

from PyQt5 import (QtCore)
import os

class Model(Store):
	
	def __init__(self, parent):
		
		Store.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.save_thread = SaveThread(self)
	
	def save(self):
		
		self.save_thread.wait()
		self.save_thread.start()
	
	def on_close(self):
		
		self.save_thread.wait()
	
class SaveThread(QtCore.QThread):
	
	def __init__(self, model):
		
		self.model = model
		
		QtCore.QThread.__init__(self)
	
	def run(self):
		
		if not self.model.data_source is None:
			self.model.data_source.save()
