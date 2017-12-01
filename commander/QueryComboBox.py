from PyQt5 import (QtWidgets)

class QueryComboBox(QtWidgets.QComboBox):
	
	def __init__(self):
		
		super(QueryComboBox, self).__init__()
		self.setEditable(True)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.setMinimumHeight(26)
		self.setAcceptDrops(True)
	
	def dragEnterEvent(self, event):
		# TODO
		
		pass
	
	def dropEvent(self, event): # TODO
		# TODO this function is never called! override QtWidgets.QComboBox.lineEdit to catch drop events
		
		pass

