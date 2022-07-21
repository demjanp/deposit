from deposit.store.abstract_dtype import AbstractDType

class DResource(AbstractDType):
	
	def __init__(self, value = None):
		
		AbstractDType.__init__(self, value)
		
		self._objects = set()
	
	@property
	def url(self):
		
		return self.get_value()[0]
	
	@property
	def filename(self):
		
		return self.get_value()[1]
		
	@property
	def is_stored(self):
		
		return (self.get_value()[2] == True)
	
	@property
	def is_image(self):
		
		return (self.get_value()[3] == True)
	
	@property
	def object_ids(self):
		# ids of Objects which have resource as a Descriptor
		
		return self._objects
	
	def get_value(self):
		# return (url, filename, is_stored, is_image)
		
		value = AbstractDType.get_value(self)
		if value is None:
			AbstractDType.set_value(self, (None, None, False, False))
		else:
			pass
		return AbstractDType.get_value(self)
	
	def set_value(self, value):
		# value = (url / path, filename, is_stored, is_image)
		
		if value is None:
			AbstractDType.set_value(self, (None, None, False, False))
			return
		
		if (not isinstance(value, tuple)) or (len(value) != 4):
			raise Exception("Invalid value specified: %s" % (str(value)))
		
		AbstractDType.set_value(self, value)
	
	def add_object(self, obj_id):
		
		self._objects.add(obj_id)
	
	def del_object(self, obj_id):
		
		if obj_id in self._objects:
			self._objects.remove(obj_id)
	
	def to_dict(self):
		
		return dict(
			dtype = self.__class__.__name__,
			value = self._value,
			objects = list(self._objects),
		)
	
	def from_dict(self, data):
		
		self._value = data["value"]
		self._objects = set(data["objects"])
		
		return self
	
	def __str__(self):
		
		url, _, _, _ = AbstractDType.get_value(self)
		
		return "%s(%s)" % (self.__class__.__name__, str(url))
