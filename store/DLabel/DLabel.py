import sys

class DLabel(object):

	def __init__(self, value):

		self._value = value

	def __str__(self):

		return "%s('%s')" % (self.__class__.__name__, self._value)

	def __repr__(self):

		value = self.__str__()
		if not value is None:
			value = value.encode("utf-8")
		return value

	def __eq__(self, other):

		return isinstance(other, DLabel) and (self._value == other._value)

	@property
	def value(self):
		# string format

		return self._value

	@property
	def query_value(self):
		# value to use when evaluating query

		return self._value
	
	def asdtype(self, dtype, *args, **kwargs):
		# convert this label to other dtype (DString / DDateTime / DResource / DGeometry / DNone)
		
		return getattr(sys.modules["deposit.store.DLabel.%s" % (dtype)], dtype)(self._value, *args, **kwargs)
	
	def to_dict(self):

		return dict(
			dtype = self.__class__.__name__,
			value = self._value,
		)

	def from_dict(self, data):

		self._value = data["value"]
		
		return self
