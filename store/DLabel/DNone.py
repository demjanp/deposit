from deposit.store.DLabel.DLabel import (DLabel)

class DNone(DLabel):
	# public properties:
	#	value = None

	def __init__(self, value = None):

		super(DNone, self).__init__(None)

	@property
	def value(self):
		# None

		return None

	def __str__(self):

		return ""

	def to_dict(self):

		return dict(
			dtype = "DNone",
		)

	def from_dict(self, *args):

		return self

