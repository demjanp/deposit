from deposit import Broadcasts
from deposit.DModule import (DModule)
import time

class DataSource(DModule):
	
	def __init__(self, store):

		self.store = store
		self.identifier = None
		self.url = None
		self.connstr = None
		self.is_busy = False
		
		DModule.__init__(self)
	
	@property
	def name(self):
		
		return self.__class__.__name__
	
	def set_identifier(self, identifier):

		self.identifier = identifier
		if self.store.data_source == self:
			self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)
	
	def wait_if_busy(self, timeout = 5):
		
		t0 = time.time()
		while self.is_busy:
			time.sleep(0.1)
			if time.time() - t0 > timeout:
				self.is_busy = False
				return False
		return True
	
	def set_url(self, url):
		# re-implement
		
		pass
	
	def set_connstr(self, connstr):
		# re-implement
		
		pass
	
	def is_valid(self):
		# re-implement
		
		return False
	
	def load(self):
		# re-implement
		
		return False
	
	def link(self):
		# re-implement
		
		return False
		
	def save(self):
		# re-implement
		
		return False
