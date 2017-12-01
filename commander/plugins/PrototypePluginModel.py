
class PrototypePluginModel(object):
	
	def __init__(self, parent_model):
		
		self._parent_model = parent_model
		self._view = None
		
		super(PrototypePluginModel, self).__init__()
	
	@property
	def store_changed(self):
		# store_changed(ids); ids = {created: [id, uri, ...], updated: [id, uri, ...], deleted: [id, uri, ...], ordered: [id, uri, ...]}
		
		return self._parent_model.store_changed
	
	def parent_model(self):
		
		return self._parent_model
	
	def has_store(self):
		
		return self._parent_model.has_store()
	
	def set_view(self, view):
		
		self._view = view
