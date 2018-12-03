from deposit.store.DLabel.DLabel import (DLabel)

class DString(DLabel):
	# constructor attributes:
	#	value: str compatible type
	# public properties:
	#	value = string format

	def __init__(self, value):
		
		super(DString, self).__init__(str(value))

