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
	
	def to_dict(self):
		
		return dict(
			data_source_class = self.__class__.__name__,
			identifier = self.identifier,
			url = self.url,
			connstr = self.connstr,
			local_folder = self.store.local_folder,
			changed = self.store.changed,
			classes = self.store.classes.to_dict(), # {name: class data, ...}
			objects = self.store.objects.to_dict(), # {id: object data, ...}
			events = self.store.events.to_list(),
			user_tools = self.store.user_tools.to_list(),
			queries = self.store.queries.to_dict(),
		)
	
	def from_dict(self, data):
		
		self.identifier = data["identifier"]
		self.url = data["url"]
		self.connstr = data["connstr"]
		self.store.local_folder = data["local_folder"]
		self.store.changed = data["changed"]
		data["objects"] = dict([(int(id), data["objects"][id]) for id in data["objects"]])
		self.store.classes.from_dict(data["classes"])
		self.store.objects.from_dict(data["objects"])
		self.store.events.from_list(data["events"])
		self.store.user_tools.from_list(data["user_tools"])
		self.store.queries.from_dict(data["queries"])
	
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
