from deposit.store.DLabel.DLabel import (DLabel)

class DDateTime(DLabel):

	def __init__(self, value):

		self._value = self.__convert_value(value)

		super(DDateTime, self).__init__(self._value)

	def __convert_value(self, value):

		return str(value)

