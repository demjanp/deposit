from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools.Query import (Query)

from PySide2 import (QtWidgets, QtCore, QtGui)

class EditorQuery(ViewChild, QtWidgets.QDialog):
	
	def __init__(self, model, view, query_tool):
		
		self.query_tool = query_tool
		
		ViewChild.__init__(self, model, view)
		QtWidgets.QDialog.__init__(self, self.view)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.setWindowTitle("Edit Query Tool")
		
		self.setMinimumWidth(600)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.title_edit = QtWidgets.QLineEdit()
		self.query_edit = QtWidgets.QPlainTextEdit()
		form = QtWidgets.QFrame()
		form.setLayout(QtWidgets.QFormLayout())
		form.layout().setContentsMargins(0, 0, 0, 0)
		form.layout().addRow("Title:", self.title_edit)
		form.layout().addRow("Query:", self.query_edit)
		self.layout().addWidget(form)
		
		self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal)
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		self.layout().addWidget(self.buttonBox)
		
		self.finished.connect(self.on_finished)
		
		self.set_up()
	
	def set_up(self):
		
		if self.query_tool is not None:
			self.title_edit.setText(self.query_tool.label)
			self.query_edit.setPlainText(self.query_tool.value)
	
	def save(self):
		
		title = self.title_edit.text()
		querystr = self.query_edit.toPlainText()
		if title and querystr:
			query = Query(title, querystr, self.view)
			if self.query_tool is None:
				self.view.usertools.add_tool(query)
			else:
				self.view.usertools.update_tool(self.query_tool.label, query)
	
	def on_finished(self, code):
		
		if code == QtWidgets.QDialog.Accepted:
			self.save()