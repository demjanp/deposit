'''
	Deposit Commander
	--------------------------
	
	Created on 30. 9. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	GUI to CRUD functions of a Deposit Store
	
'''

from PyQt5 import (QtWidgets)
import sys

from deposit.commander.MainWindowModel import MainWindowModel
from deposit.commander.MainWindowView import MainWindowView

class Commander(object):
	# main Deposit Commander class
	
	def __init__(self):
		
		app = QtWidgets.QApplication(sys.argv)
		model = MainWindowModel()
		view = MainWindowView()
		model.set_view(view)
		view.set_model(model)
		view.show()
		app.exec_()
