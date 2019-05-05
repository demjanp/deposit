from deposit import Broadcasts
from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class AddQuery(Dialog):
	
	def title(self):

		return "Add Query"
	
	def set_up(self, querystr):
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.title_edit = QtWidgets.QLineEdit()
		self.query_edit = QtWidgets.QPlainTextEdit()
		if querystr:
			self.query_edit.setPlainText(querystr)
		form = QtWidgets.QFrame()
		form.setLayout(QtWidgets.QFormLayout())
		form.layout().setContentsMargins(0, 0, 0, 0)
		form.layout().addRow("Title:", self.title_edit)
		form.layout().addRow("Query:", self.query_edit)
		self.layout().addWidget(form)
	
	def process(self):
		
		title = self.title_edit.text()
		querystr = self.query_edit.toPlainText()
		if title and querystr:
			self.model.queries.set(title, querystr)

