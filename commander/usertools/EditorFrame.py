from deposit.commander.usertools import (EditorControls)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class EditorFrame(QtWidgets.QFrame):
	
	def __init__(self, element, form_editor, user_control = None):
		
		self.label_edit = None
		self.ctrl = None
		self.selected = False
		self.form_editor = form_editor
		
		QtWidgets.QFrame.__init__(self)
		
		self.setStyleSheet("%s:hover {background: grey;}" % (self.__class__.__name__))
		self.setLayout(QtWidgets.QFormLayout())
		
		self.ctrl = getattr(EditorControls, element)(user_control)
		self.label_edit = QtWidgets.QLineEdit(self.ctrl.user_control.label)
		self.layout().addRow(self.label_edit, self.ctrl)
	
	def user_element(self):
		
		label = self.label_edit.text()
		select = self.ctrl.select_text()
		
		if (not label) or (not select):
			return None
		select = select.split(".")
		if len(select) != 2:
			return None
		
		self.ctrl.user_control.label = label
		self.ctrl.user_control.dclass = select[0]
		self.ctrl.user_control.descriptor = select[1]
		return self.ctrl.user_control
	
	def setSelected(self, state):
		
		if state:
			self.setStyleSheet("%s {border: 2px solid grey;} %s:hover {background: grey;}" % (self.__class__.__name__, self.__class__.__name__))
		else:
			self.setStyleSheet("%s:hover {background: grey;}" % (self.__class__.__name__))
		self.selected = state
	
	def mousePressEvent(self, event):
		
		state = not self.selected
		form_editor = self.form_editor
		if hasattr(form_editor, "form_editor"):
			form_editor = form_editor.form_editor
		form_editor.deselect_all()
		self.setSelected(state)
		form_editor.on_selection_changed()

