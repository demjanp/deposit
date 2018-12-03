from deposit.commander.frames._Frame import (Frame)

from PyQt5 import (QtCore, QtWidgets, QtGui)

class DatabaseList(Frame, QtWidgets.QListWidget):
	
	def __init__(self, model, view, parent):
		
		self.class_names = []
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QListWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		pass
	
	