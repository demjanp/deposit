from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class External(Frame):
	
	def __init__(self, model, view, parent, es):
		
		self.es = es
		self.header = None
		self.body = None
		
		Frame.__init__(self, model, view, parent)
	
	def get_current_header(self):
		
		return self.header
	
	def get_current_body(self):
		
		return self.body
	
	def get_targets(self):
		
		header = self.get_current_header()
		targets = {}  # {column_idx: target, ...}
		for idx in range(self.es.column_count(header.sheet)):
			targets[idx] = header.item(0, idx).data(QtCore.Qt.DisplayRole)
		return targets
	
	def import_data(self, relations = []):
		
		header = self.get_current_header()
		targets = self.get_targets()
		self.es.import_data(header.sheet, targets, relations)

