from deposit.store.abstract_dtype import AbstractDType
import datetime

class DDateTime(AbstractDType):
	
	@property
	def isoformat(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, str):
			return value
		if isinstance(value, datetime.datetime):
			return value.isoformat()
		return None
	
	def get_value(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, str):
			AbstractDType.set_value(self, datetime.datetime.fromisoformat(value))
		return AbstractDType.get_value(self)
	
	def set_value(self, value):
		
		if isinstance(value, DDateTime):
			AbstractDType.set_value(self, value.value)
			return
		AbstractDType.set_value(self, value)
	
	def to_dict(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, datetime.datetime):
			value = value.isoformat()
		
		return dict(
			dtype = self.__class__.__name__,
			value = value,
		)
	
	def __str__(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, datetime.datetime):
			value = value.isoformat()
		
		return "%s(%s)" % (self.__class__.__name__, value)
