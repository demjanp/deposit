from deposit.commander.View import (View)

from PyQt5 import (QtWidgets)
import sys

class Commander(object):

	# main Deposit Commander class
	
	def __init__(self):
		
		app = QtWidgets.QApplication(sys.argv)

		self.view = View()
		
		self.view.show()
		app.exec_()
