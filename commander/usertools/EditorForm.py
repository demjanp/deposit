from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools.EditorFrame import (EditorFrame)
from deposit.commander.usertools.EditorGroup import (EditorGroup)
from deposit.commander.usertools.EditorSelect import (EditorSelect)
from deposit.commander.usertools.EditorColumn import (EditorColumn)
from deposit.commander.usertools.EditorActions import (Action)
from deposit.commander.usertools import (EditorActions)
from deposit.commander.usertools.SearchForm import (SearchForm)
from deposit.commander.usertools.EntryForm import (EntryForm)
from deposit.commander.usertools.UserControls import (UserControl, Select)
from deposit.commander.usertools.ColumnBreak import (ColumnBreak)
from deposit.commander.usertools.UserGroups import (Group)

from PySide2 import (QtWidgets, QtCore, QtGui)

class EditorForm(ViewChild, QtWidgets.QMainWindow):
	
	def __init__(self, model, view, form_tool, entry):
		
		self.entry = entry
		self.form_tool = form_tool
		self.columns = []
		
		ViewChild.__init__(self, model, view)
		QtWidgets.QMainWindow.__init__(self)
		
		self.central_widget = QtWidgets.QWidget(self)
		self.central_widget.setLayout(QtWidgets.QVBoxLayout())
		self.setCentralWidget(self.central_widget)
		
		self.setStyleSheet("font: 14px;")
		
		self.title_frame = QtWidgets.QFrame()
		self.title_frame.setLayout(QtWidgets.QHBoxLayout())
		self.title_frame.layout().setContentsMargins(0, 0, 0, 0)
		self.title_frame.layout().addWidget(QtWidgets.QLabel("Title:"))
		self.title_edit = QtWidgets.QLineEdit()
		self.title_frame.layout().addWidget(self.title_edit)
		self.central_widget.layout().addWidget(self.title_frame)
		
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QHBoxLayout())
		self.controls_frame.layout().setContentsMargins(10, 10, 10, 10)
		
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_area.setWidget(self.controls_frame)
		
		self.central_widget.layout().addWidget(scroll_area)
		
		self.selects_frame = QtWidgets.QFrame()
		self.selects_frame.setLayout(QtWidgets.QHBoxLayout())
		self.selects_frame.layout().setContentsMargins(10, 10, 10, 10)
		if not self.entry:
			self.selects_frame.layout().addWidget(QtWidgets.QLabel("SELECT"))
			self.selects_frame.layout().addStretch()
		self.central_widget.layout().addWidget(self.selects_frame)
		
		self.setWindowTitle("Entry Form Editor")
		self.setWindowIcon(self.view.get_icon("form.svg"))
		
		self.toolbar = self.addToolBar("Toolbar")
		self.toolbar.setIconSize(QtCore.QSize(36,36))
		
		for key in EditorActions.__dict__:
			action = getattr(EditorActions, key)
			if not isinstance(action, type):
				continue
			if key.startswith("_Separator"):
				self.toolbar.addSeparator()
				continue
			if (action == Action) or (not issubclass(action, Action)):
				continue
			self.toolbar.addAction(action(self))
		
		self.set_up()
		
		button_frame = QtWidgets.QFrame()
		button_frame.setLayout(QtWidgets.QHBoxLayout())
		button_frame.layout().setContentsMargins(5, 5, 5, 5)
		button_frame.layout().addStretch()
		button_save = QtWidgets.QPushButton("Save")
		button_save.clicked.connect(self.on_save)
		button_frame.layout().addWidget(button_save)
		button_cancel = QtWidgets.QPushButton("Cancel")
		button_cancel.clicked.connect(self.on_cancel)
		button_frame.layout().addWidget(button_cancel)
		self.central_widget.layout().addWidget(button_frame)
	
	def set_up(self):
		
		if self.form_tool is not None:
			self.title_edit.setText(self.form_tool.label)
			for element in self.form_tool.elements:
				if issubclass(element.__class__, Select):
					self.add_select(element)
				elif isinstance(element, ColumnBreak):
					self.add_column()
				elif issubclass(element.__class__, UserControl):
					self.add_frame(element.__class__.__name__, element)
				elif issubclass(element.__class__, Group):
					self.add_group(element.__class__.__name__, element)
		
		if not self.columns:
			self.add_column()
		
		self.update_toolbar()
	
	def get_selected(self):
		
		for column in self.columns:
			for element in column.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
				if isinstance(element, EditorGroup) or isinstance(element, EditorFrame):
					if element.selected:
						return element
					if isinstance(element, EditorGroup):
						element = element.get_selected()
						if element is not None:
							return element
		for element in self.selects_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorSelect):
				if element.selected:
					return element
		return None
	
	def deselect_all(self):
		
		for element in self.controls_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorGroup) or isinstance(element, EditorFrame):
				element.setSelected(False)
				if isinstance(element, EditorGroup):
					element.deselect_all()
		for element in self.selects_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
			if isinstance(element, EditorSelect):
				element.setSelected(False)
	
	def update_toolbar(self):
		
		selected = self.get_selected()
		for action in self.toolbar.actions():
			if action.isSeparator():
				continue
			action.update()
	
	def get_control_index(self, element):
		
		for column in self.columns:
			idx = column.layout().indexOf(element)
		return column, idx
	
	def add_column(self):
		
		self.columns.append(EditorColumn())
		self.controls_frame.layout().addWidget(self.columns[-1])
	
	def add_frame(self, element, user_control = None):
		
		selected = self.get_selected()
		if isinstance(selected, EditorGroup):
			selected.add_frame(element)
		elif isinstance(selected, EditorFrame):
			if selected.form_editor == self:
				column, idx = self.get_control_index(selected)
				column.layout().insertWidget(idx, EditorFrame(element, self, user_control))
			else:
				selected.form_editor.add_frame(element, before = selected)
		else:
			self.columns[-1].layout().addWidget(EditorFrame(element, self, user_control))
	
	def add_group(self, element, user_group = None):
		
		selected = self.get_selected()
		idx = None
		if (selected is None) or (not isinstance(selected, EditorSelect)):
			if (selected is not None) and (selected.form_editor == self):
				column, idx = self.get_control_index(selected)
		if idx is None:
			self.columns[-1].layout().addWidget(EditorGroup(element, self, user_group))
		else:
			column.layout().insertWidget(idx, EditorGroup(element, self, user_group))
	
	def add_select(self, user_select = None):
		
		selected = self.get_selected()
		if selected is not None:
			idx = self.selects_frame.layout().indexOf(selected)
		else:
			idx = self.selects_frame.layout().count() - 1
		self.selects_frame.layout().insertWidget(idx, EditorSelect(self, user_select))
	
	def remove_control(self, element):
		
		column, _ = self.get_control_index(element)
		column.layout().removeWidget(element)
	
	def delete(self):
		
		selected = self.get_selected()
		if selected is None:
			return
		if isinstance(selected, EditorFrame):
			selected.form_editor.remove_control(selected)
		elif isinstance(selected, EditorGroup):
			self.remove_control(selected)
		elif isinstance(selected, EditorSelect):
			self.selects_frame.layout().removeWidget(selected)
		selected.selected = False
		selected.setParent(None)
		self.update_toolbar()
	
	def save(self):
		
		if self.entry:
			Form = EntryForm
		else:
			Form = SearchForm
		title = self.title_edit.text()
		if title:
			form = Form(title, self.view)
			for column in self.columns:
				form.elements.append(column.user_element())
				for element in column.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
					if element.parent() != column:
						continue
					if isinstance(element, EditorGroup) or isinstance(element, EditorFrame):
						form.elements.append(element.user_element())
			for element in self.selects_frame.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
				if isinstance(element, EditorSelect):
					form.elements.append(element.user_element())
			if self.form_tool is None:
				self.view.usertools.add_tool(form)
			else:
				self.view.usertools.update_tool(self.form_tool.label, form)
	
	def stop(self):
		
		self.view.usertools.manager.hide()
	
	def closeEvent(self, event):
		
		self.stop()
	
	def on_selection_changed(self):
		
		self.update_toolbar()
	
	def on_save(self, *args):
		
		self.save()
		self.close()
	
	def on_cancel(self, *args):
		
		self.close()

