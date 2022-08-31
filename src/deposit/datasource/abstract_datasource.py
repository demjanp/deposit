
class AbstractDatasource(object):
	
	def __init__(self):
		
		self._progress = None
	
	def to_dict(self):
		
		return dict(
			datasource = self.__class__.__name__,
			url = None,
			identifier = None,
			connstr = None,
		)
	
	def get_name(self):
		
		return "data"
	
	def set_progress(self, progress):
		
		self._progress = progress
	
	def close_progress(self):
		
		if self._progress is not None:
			self._progress.cancel()
	
	def update_progress(self, value, maximum = None, text = None):
		
		if self._progress is not None:
			self._progress.update_state(text = text, value = value, maximum = maximum)
	
	def progress_cancelled(self):
		
		if self._progress is not None:
			return self._progress.cancel_pressed()
		return False
	
	def is_valid(self):
		
		return False
	
	def can_create(self):
		
		return False
	
	def get_folder(self):
		
		return None
	
	def create(self, *args, **kwargs):
		
		pass
	
	def backup(self, store, folder):
		
		pass
	
	def save(self, store, progress = None, *args, **kwargs):
		
		pass
	
	def load(self, store, progress = None, *args, **kwargs):
		
		pass
	
	def __str__(self):
		
		return self.__class__.__name__
