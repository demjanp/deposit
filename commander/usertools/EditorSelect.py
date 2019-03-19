from deposit.commander.usertools.UserControls import (Select)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class EditorSelect(QtWidgets.QFrame):
	
	def __init__(self, form_editor, user_select = None):
		
		self.label_edit = None
		self.user_select = None
		self.selected = False
		self.form_editor = form_editor
		
		QtWidgets.QFrame.__init__(self)
		
		if user_select is None:
			user_select = Select("", "", "Class", "Descriptor")
		self.user_select = user_select
		
		self.setStyleSheet("%s:hover {background: grey;}" % (self.__class__.__name__))
		self.setLayout(QtWidgets.QHBoxLayout())
		
		self.select = QtWidgets.QLineEdit("%s.%s" % (self.user_select.dclass, self.user_select.descriptor))
		self.layout().addWidget(self.select)
	
	def select_text(self):
		
		return self.select.text().strip()
	
	def user_element(self):
		
		select = self.select_text()
		if not select:
			return None
		select = select.split(".")
		if len(select) != 2:
			return None
		
		self.user_select.dclass = select[0]
		self.user_select.descriptor = select[1]
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

