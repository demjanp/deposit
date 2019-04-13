from deposit.commander.usertools import (UserGroups)
from deposit.commander.usertools.EditorFrame import (EditorFrame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class EditorGroup(QtWidgets.QGroupBox):
	
	def __init__(self, element, form_editor, user_group = None):
		
		self.label_edit = None
		self.element = element
		self.group = None
		self.hovered = False
		self.selected = False
		self.bold = False
		self.form_editor = form_editor
		
		QtWidgets.QGroupBox.__init__(self, self.element)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		if user_group is None:
			user_group = getattr(UserGroups, element)("", "Label")
		self.group = user_group
		
		self.label_edit = QtWidgets.QLineEdit(self.group.label)
		form = QtWidgets.QFrame()
		form.setLayout(QtWidgets.QFormLayout())
		form.layout().setContentsMargins(0, 0, 0, 0)
		form.layout().addRow("Label:", self.label_edit)
		self.layout().addWidget(form)
		
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QVBoxLayout())
		self.controls_frame.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().addWidget(self.controls_frame)
		
		for member in self.group.members:
			self.add_frame(member.__class__.__name__, member)
		
		self.bold = "font-weight: bold;" in self.group.stylesheet
		
		self.update_stylesheet()
		
		self.setMouseTracking(True)
	
	def add_frame(self, element, user_control = None, before = None):
		
		if before is None:
			self.controls_frame.layout().addWidget(EditorFrame(element, self, user_control))
		else:
			idx = self.controls_frame.layout().indexOf(before)
			self.controls_frame.layout().insertWidget(idx, EditorFrame(element, self, user_control))
	
	def remove_control(self, element):
		
		self.controls_frame.layout().removeWidget(element)
	
	def user_element(self):
		
		label = self.label_edit.text()
		if not label:
			return None
		self.group.label = label
		self.group.stylesheet = "QGroupBox {font-weight: bold;}" if self.bold else ""
		self.group.members = []
		for element in self.controls_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorFrame):
				self.group.members.append(element.user_element())
		return self.group
		
	def get_selected(self):
		
		for element in self.controls_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorFrame):
				if element.selected:
					return element
		return None
		
	def deselect_all(self):
		
		for element in self.controls_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorFrame):
				element.setSelected(False)
	
	def update_stylesheet(self):
		
		stylesheet = ""
		if self.hovered:
			stylesheet += "%s {background: lightgrey;}" % (self.__class__.__name__)
		if self.selected:
			stylesheet += " %s {border: 2px solid grey;}" % (self.__class__.__name__)
		if self.bold:
			stylesheet += " %s {font-weight: bold;}" % (self.__class__.__name__)
		self.setStyleSheet(stylesheet)
	
	def setSelected(self, state):
		
		self.selected = state
		self.update_stylesheet()
		self.form_editor.on_selection_changed()
	
	def setBold(self, state):
		
		self.bold = state
		self.update_stylesheet()
	
	def enterEvent(self, event):
		
		self.hovered = True
		self.update_stylesheet()
	
	def leaveEvent(self, event):
		
		self.hovered = False
		self.update_stylesheet()
		
	def mousePressEvent(self, event):
		
		state = not self.selected
		self.form_editor.deselect_all()
		self.setSelected(state)
		self.form_editor.on_selection_changed()

