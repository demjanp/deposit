from deposit import Broadcasts
from deposit.commander.frames.External.External import External
from deposit.commander.frames.External.ExternalHeader import ExternalHeader
from deposit.commander.frames.External.ExternalLst import ExternalLst
from deposit.commander.frames.XLSXMembers.XLSXSheet import XLSXSheet

from PySide2 import (QtWidgets, QtCore, QtGui)

class XLSX(External, QtWidgets.QTabWidget):

	def __init__(self, model, view, parent, es):
		
		External.__init__(self, model, view, parent, es)
		QtWidgets.QTabWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		for sheet_name in self.es.sheets():
			header = ExternalHeader(self, self.es, sheet_name)
			body = ExternalLst(self, self.es, sheet_name)
			sheet = XLSXSheet(header, body)
			self.addTab(sheet, sheet_name)
	
	def get_current_header(self):
		
		return self.currentWidget().header
	
	def get_current_body(self):
		
		return self.currentWidget().body
	
	def name(self):
		
		return self.es.url
	
	def icon(self):
		
		return "xlsxfile.svg"
	
	