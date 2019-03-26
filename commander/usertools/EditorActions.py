
from PyQt5 import (QtWidgets, QtCore, QtGui)

class Action(QtWidgets.QAction):
	
	def __init__(self, form_editor):
		
		self.form_editor = form_editor
		
		QtWidgets.QAction.__init__(self, self.form_editor.view)
		
		self.setText(self.name())
		icon = self.icon()
		if icon:
			icon = self.form_editor.view.get_icon(icon)
			if icon:
				self.setIcon(icon)
		self.setToolTip(self.help())
		self.setCheckable(self.checkable())
		self.triggered.connect(self.on_triggered)
	
	def name(self):
		
		return self.__class__.__name__
	
	def icon(self):
		
		return ".svg"
	
	def help(self):
		
		return self.name()
	
	def enabled(self):
		
		return True
	
	def checkable(self):
		
		return False
	
	def checked(self):
		
		return False
	
	def visible(self):
		
		return True
	
	def update(self):
		
		self.setEnabled(self.enabled())
		self.setVisible(self.visible())
		self.setChecked(self.checked())
	
	def on_triggered(self, state):
		
		pass

class LineEdit(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "line_edit.svg"
	
	def on_triggered(self, state):
		
		self.form_editor.add_frame(self.__class__.__name__)

class PlainTextEdit(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "plain_text_edit.svg"
	
	def enabled(self):
		
		return self.form_editor.entry
	
	def visible(self):
		
		return self.form_editor.entry
	
	def on_triggered(self, state):
		
		self.form_editor.add_frame(self.__class__.__name__)

class ComboBox(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "combo_box.svg"
	
	def on_triggered(self, state):
		
		self.form_editor.add_frame(self.__class__.__name__)

class CheckBox(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "check_box.svg"
	
	def enabled(self):
		
		return self.form_editor.entry
	
	def visible(self):
		
		return self.form_editor.entry
	
	def on_triggered(self, state):
		
		self.form_editor.add_frame(self.__class__.__name__)

class Group(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "group_box.svg"
	
	def enabled(self):
		
		return self.form_editor.entry
		
	def visible(self):
		
		return self.form_editor.entry

	def on_triggered(self, state):
		
		self.form_editor.add_group(self.__class__.__name__)

class MultiGroup(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "multi_group_box.svg"
	
	def enabled(self):
		
		return self.form_editor.entry
		
	def visible(self):
		
		return self.form_editor.entry

	def on_triggered(self, state):
		
		self.form_editor.add_group(self.__class__.__name__)

class ColumnBreak(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "column_break.svg"
	
	def on_triggered(self, state):
		
		self.form_editor.add_column()

class Select(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "select.svg"
	
	def enabled(self):
		
		return not self.form_editor.entry
		
	def visible(self):
		
		return not self.form_editor.entry

	def on_triggered(self, state):
		
		self.form_editor.add_select()

class _Separator1(): pass

class Bold(Action):
	
	def icon(self):
		
		return "bold.svg"
	
	def enabled(self):
		
		return self.form_editor.get_selected().__class__.__name__ in ["EditorFrame", "EditorGroup"]
	
	def checkable(self):
		
		return True
	
	def checked(self):
		
		if self.form_editor.get_selected().__class__.__name__ not in ["EditorFrame", "EditorGroup"]:
			return False
		return self.form_editor.get_selected().bold
	
	def on_triggered(self, state):
		
		self.form_editor.get_selected().setBold(state)

class OrderUp(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "up_small_black.svg"
	
	def enabled(self):
		
		return self.form_editor.get_selected() is not None
	
	def on_triggered(self, state):
		
		pass

class OrderDown(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "down_small_black.svg"
	
	def enabled(self):
		
		return self.form_editor.get_selected() is not None
	
	def on_triggered(self, state):
		
		pass

class Delete(Action):
	
	def __init__(self, form_editor):
		
		Action.__init__(self, form_editor)
	
	def icon(self):
		
		return "delete.svg"
	
	def enabled(self):
		
		return self.form_editor.get_selected() is not None
	
	def on_triggered(self, state):
		
		self.form_editor.delete()

