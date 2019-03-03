from deposit.commander.View import (View)

class Commander(object):

	# main Deposit Commander class
	
	def __init__(self, model = None):
		
		self.view = View(model)
		self.view.show()
