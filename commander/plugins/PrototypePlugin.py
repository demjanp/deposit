
class PrototypePlugin(object):
	
	def __init__(self, parent_view, **kwargs):
		
		self._parent_view = parent_view
		self._model = None
		self._is_shown = None
		
		super(PrototypePlugin, self).__init__()
	
	def set_model(self, model):
		
		self._model = model
		self._model.store_changed.connect(self.on_store_changed)
		self.on_set_model()
	
	def on_set_model(self):
		# called after model has been set
		
		pass
	
	def on_show(self):
		
		pass
	
	def on_store_changed(self, ids):
		
		pass
	
	def on_close(self):
		
		pass
	
	def showEvent(self, event):
		
		super(PrototypePlugin, self).showEvent(event)
		if not self._is_shown:
			self._is_shown = True
			self.on_show()
	
	def closeEvent(self, event):
		
		self.on_close()
		try:
			self._model.store_changed.disconnect(self.on_store_changed)
		except:
			pass
		self._model = None
		super(PrototypePlugin, self).closeEvent(event)
		self._parent_view.on_plugin_close(self)
