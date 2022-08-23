class AbstractDType(object):
	
	def __init__(self, value = None, *args, **kwargs):
		
		self.set_value(value)
	
	@property
	def value(self):
		
		return self.get_value()
	
	@value.setter
	def value(self, value):
		
		self.set_value(value)
	
	def get_value(self):
		
		return self._value
	
	def set_value(self, value):
		
		self._value = value
	
	def to_dict(self):
		
		return dict(
			dtype = self.__class__.__name__,
			value = self._value,
		)
	
	def from_dict(self, data):
		
		self._value = data["value"]
		
		return self
		
	def __str__(self):
		
		return "%s(%s)" % (self.__class__.__name__, str(self.get_value()))
	
	def __repr__(self):
	
		return self.__str__()
	
	def __eq__(self, other):
		
		return (self.__class__ == other.__class__) and (self.get_value() == other.get_value())

