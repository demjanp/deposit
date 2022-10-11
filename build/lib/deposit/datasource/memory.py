from deposit.datasource.abstract_datasource import AbstractDatasource

from deposit.utils.fnc_files import (get_temp_path)
import uuid

class Memory(AbstractDatasource):
	
	def __init__(self):
		
		AbstractDatasource.__init__(self)
		
		self._uuid = uuid.uuid4().hex
	
	def get_name(self):
		
		return "memory db"
	
	def is_valid(self):
		
		return True
	
	def can_create(self):
		
		return True
	
	def get_folder(self):
		
		return get_temp_path(self._uuid)
	
	def create(self, *args, **kwargs):
		
		return True
	
	def save(self, store, progress = None, *args, **kwargs):
		
		return True
	
	def load(self, store, progress = None, *args, **kwargs):
		
		store.clear()
		store.set_datasource(self)
		
		return True
