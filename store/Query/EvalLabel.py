
def l(other):
	if isinstance(other, EvalLabel):
		return other._l
	return other

STRING_METHODS = [name for name in dir("") if not name.startswith("__")] # all string methods

class EvalLabel():
	
	def __init__(self, label):
		
		self._l = self.__convert_value(label)

	def __convert_value(self, value):
		
		if value is None:
			return value
		if not (isinstance(value, str) and ("_" in value)):
			try:
				value = float(value)
				if value - int(value) == 0:
					return int(value)
				return value
			except:
				pass
		return str(value)
	
	
	# Methematical
	
	def __add__(self, other): # +
		
		other = l(other)
		if self._l is None:
			return other
		if other is None:
			return self._l
		if isinstance(other, str):
			return str(self._l) + other
		if isinstance(self._l, str):
			return self._l + str(other)
		return self._l + other
	
	def _numbers(self, val):
		
		return not (isinstance(self._l, str) or (self._l is None) or isinstance(val, str) or (val is None))
	
	def __sub__(self, other): # -
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l - other
	
	def __mul__(self, other): # *
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l * other
	
	def __pow__(self, other): # **
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l ** other
	
	def __truediv__(self, other): # /
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l / other
	
	def __mod__(self, other): # %
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l % other
	
	def __floordiv__(self, other): # //
		
		other = l(other)
		if not self._numbers(other):
			return None
		return self._l // other
	
	def __abs__(self):
		
		if isinstance(self._l, str) or (self._l is None):
			return self._l
		return abs(self._l)
	
	
	# Logical
	
	def __bool__(self):
		
		if isinstance(self._l, str):
			return (self._l != "")
		if self._l is None:
			return False
		return (self._l != 0)
	
	
	# Comparison
	
	def __lt__(self, other): # <
		
		other = l(other)
		if not self._numbers(other):
			return False
		return self._l < other
	
	def __le__(self, other): # <=
		
		other = l(other)
		if not self._numbers(other):
			return False
		return self._l <= other
	
	def __eq__(self, other): # ==
		
		other = l(other)
		if (self._l is None) or (other is None):
			return self._l == other
		if isinstance(other, str):
			return str(self._l) == other
		if isinstance(self._l, str):
			return self._l == str(other)
		return self._l == other
	
	def __ne__(self, other): # !=
		
		return self._l != l(other)
	
	def __gt__(self, other): # >
		
		other = l(other)
		if not self._numbers(other):
			return False
		return self._l > other
	
	def __ge__(self, other): # >=
		
		other = l(other)
		if not self._numbers(other):
			return False
		return self._l >= other
	
	
	# Sequence
	
	def __getitem__(self, index): # [index]
		
		if isinstance(self._l, str) and (len(self._l) < index):
			return self._l[index]
		return None
	
	def __contains__(self, other): # in
		
		if self._l is None:
			return None
		return str(l(other)) in str(self._l)
	
	def __len__(self): # len(self)
		
		if (self._l is None):
			return 0
		return len(str(self._l))
	
	
	# String methods
	
	def __getattribute__(self, name): # e.g. (Class.Descriptor).startswith("a")
		
		if name in STRING_METHODS:
			return self.get_string_method(name)
		return object.__getattribute__(self, name)
	
	def get_string_method(self, name):
		
		def string_method(other):
			other = l(other)
			if isinstance(other, str):
				return getattr(str(self._l), name)(str(other))
			return None
		
		return string_method
	
	def __str__(self): # str(self)
		
		return str(self._l)
	
	def __repr__(self):
		
		return str(self._l)
