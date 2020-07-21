from deposit.commander.ViewChild import (ViewChild)

from PySide2 import (QtWidgets, QtCore, QtGui)

class QueryToolbar(ViewChild):
	
	def __init__(self, model, view):
		
		self.toolbar = None
		self.query_box = None
		
		ViewChild.__init__(self, model, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.view.tool_window.addToolBarBreak()
		self.toolbar = self.view.tool_window.addToolBar("Query")
		
		self.query_box = QtWidgets.QComboBox(self.view)
		self.query_box.setEditable(True)
		self.query_box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.query_box.setMinimumHeight(26)
		self.query_box.completer().setCaseSensitivity(QtCore.Qt.CaseSensitive)
		
		label = QtWidgets.QLabel("Query: ", self.view)
		
		self.toolbar.addWidget(label)
		self.toolbar.addWidget(self.query_box)
		
		self.query_box.lineEdit().returnPressed.connect(self.on_enter)
	
	def on_enter(self):
		
		self.view.query(self.query_box.currentText())

