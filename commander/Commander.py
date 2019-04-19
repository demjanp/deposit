from deposit.commander.View import (View)

class Commander(object):

	# main Deposit Commander class
	
	def __init__(self, *args, model = None):
		
		self.view = View(model, *args)
		self.view.show()
	
	def close(self):
		
		self.view.close()
