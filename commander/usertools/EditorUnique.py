from PySide2 import (QtWidgets, QtCore, QtGui)

class EditorUnique(QtWidgets.QFrame):
	
	def __init__(self, form_editor):
		
		self.label_edit = None
		self.selected = False
		self.form_editor = form_editor
		
		QtWidgets.QFrame.__init__(self)
		
		self.setStyleSheet("%s:hover {background: grey;}" % (self.__class__.__name__))
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.unique = QtWidgets.QLineEdit()
		self.layout().addWidget(self.unique)
	
	def select_text(self):
		
		return self.unique.text().strip()
	
	def user_element(self):
		
		unique = self.select_text()
		if not unique:
			return None
		unique = unique.split(".")
		if len(unique) != 2:
			return None
		
		self.user_select.dclass = unique[0]
		self.user_select.descriptor = unique[1]
		return self.user_select
	
	def setSelected(self, state):
		
		if state:
			self.form_editor.deselect_all()
			self.setStyleSheet("%s {border: 2px solid grey;} %s:hover {background: grey;}" % (self.__class__.__name__, self.__class__.__name__))
		else:
			self.setStyleSheet("%s:hover {background: grey;}" % (self.__class__.__name__))
		self.selected = state
		self.form_editor.on_selection_changed()
	
	def mousePressEvent(self, event):
		
		self.setSelected(not self.selected)

