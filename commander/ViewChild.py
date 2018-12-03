from deposit.DModule import (DModule)

class ViewChild(DModule):
	
	def __init__(self, model, view):
		
		self.model = model
		self.view = view
		
		DModule.__init__(self)


