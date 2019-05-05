from deposit.DModule import (DModule)

class Queries(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._queries = {}
		
		DModule.__init__(self)
	
	def get(self, title):
		
		if title in self._queries:
			return self._queries[title]
		return ""
	
	def set(self, title, querystr):
		
		if not (title and querystr):
			return
		self._queries[title] = querystr
		self.store.on_data_changed()
	
	def delete(self, title):
		
		if title in self._queries:
			del self._queries[title]
			self.store.on_data_changed()
	
	def clear(self):
		
		self._queries = {}
		self.store.on_data_changed()
	
	def to_dict(self):
		
		return self._queries.copy()
	
	def from_dict(self, data):
		
		self._queries = data.copy()

