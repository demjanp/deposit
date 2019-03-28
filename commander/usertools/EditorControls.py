from deposit.commander.usertools import (UserControls)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class EditorControl(object):
	
	def __init__(self, user_control = None):
		
		if user_control is None:
			user_control = getattr(UserControls, self.__class__.__name__)("", "Label", "Class", "Descriptor")
		self.user_control = user_control
	
	def select_text(self):
		
		return ""

class LineEdit(EditorControl, QtWidgets.QLineEdit):
	
	def __init__(self, user_control = None):
		
		EditorControl.__init__(self, user_control)
		QtWidgets.QLineEdit.__init__(self)
		self.setText("%s.%s" % (self.user_control.dclass, self.user_control.descriptor))
		
	def select_text(self):
		
		return self.text().strip()

class PlainTextEdit(EditorControl, QtWidgets.QPlainTextEdit):
	
	def __init__(self, user_control = None):
		
		EditorControl.__init__(self, user_control)
		QtWidgets.QPlainTextEdit.__init__(self)
		self.setFixedHeight(100)
		self.setPlainText("%s.%s" % (self.user_control.dclass, self.user_control.descriptor))
		
	def select_text(self):
		
		return self.toPlainText().strip()

class ComboBox(EditorControl, QtWidgets.QComboBox):
	
	def __init__(self, user_control = None):
		
		EditorControl.__init__(self, user_control)
		QtWidgets.QComboBox.__init__(self)
		self.setEditable(True)
		self.setCurrentText("%s.%s" % (self.user_control.dclass, self.user_control.descriptor))
	
	def select_text(self):
		
		return self.currentText().strip()

class CheckBox(EditorControl, QtWidgets.QFrame):
	
	def __init__(self, user_control = None):
		
		EditorControl.__init__(self, user_control)
		QtWidgets.QFrame.__init__(self)
		
		self.setLayout(QtWidgets.QHBoxLayout())
		
		self.select = QtWidgets.QLineEdit("%s.%s" % (self.user_control.dclass, self.user_control.descriptor))
		self.checkbox = QtWidgets.QCheckBox()
		self.checkbox.setChecked(True)
		self.checkbox.setEnabled(False)
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().addWidget(self.checkbox)
		self.layout().addWidget(self.select)
		self.layout().addStretch()
	
	def select_text(self):
		
		return self.select.text().strip()

class Select(EditorControl, QtWidgets.QLineEdit):
	
	def __init__(self, user_control = None):
		
		EditorControl.__init__(self, user_control)
		QtWidgets.QLineEdit.__init__(self, "%s.%s" % (self.user_control.dclass, self.user_control.descriptor))
	
	def select_text(self):
		
		return self.text().strip()

