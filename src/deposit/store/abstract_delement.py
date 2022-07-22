class AbstractDElement(object):
	
	def __init__(self, store):
		
		self._store = store
	
	def to_dict(self):
		
		return dict()