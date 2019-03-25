from deposit.commander.ViewChild import (ViewChild)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class QueryToolbar(ViewChild):
	
	def __init__(self, model, view):
		
		self.toolbar = None
		self.query_box = None
		
		ViewChild.__init__(self, model, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.view.addToolBarBreak()
		self.toolbar = self.view.addToolBar("Query")
		
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
		
		querystr = self.query_box.currentText()
		if querystr:
			querystr = querystr.strip()
			if querystr.startswith("SELECT "):
				self.view.mdiarea.create("Query", querystr)
			else:
				self.model.query(querystr)

