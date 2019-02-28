from deposit.store.DLabel.DLabel import (DLabel)

class DString(DLabel):
	# constructor attributes:
	#	value: str compatible type
	# public properties:
	#	value = string format
	#	try_numeric = float or int or str or None (in this order)

	def __init__(self, value):
		
		super(DString, self).__init__(str(value))
	
	@property
	def try_numeric(self):
		
			if self._value is None:
				return self._value
			if not (isinstance(self._value, str) and ("_" in self._value)):
				try:
					self._value = float(self._value)
					if self._value - int(self._value) == 0:
						return int(self._value)
					return self._value
				except:
					pass
			return str(self._value)
