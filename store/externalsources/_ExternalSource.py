from deposit.DModule import (DModule)

class ExternalSource(DModule):
	
	def __init__(self, store):

		self.store = store

		DModule.__init__(self)
	
	@property
	def name(self):
		
		return self.__class__.__name__
	
	def import_data(self):
		# re-implement
		
		pass
	
	def export(self, objects):
		# re-implement
		
		pass
	