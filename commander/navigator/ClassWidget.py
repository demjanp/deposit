from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.navigator.ClassList import (ClassList)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class ClassWidget(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent):
		
		self.layout = None
		self.classlist = None
		self.footer = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.classlist = ClassList(self.model, self.view, self)
		self.layout.addWidget(self.classlist)
		
		self.footer = ClassFooter(self)
		self.layout.addWidget(self.footer)
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		
		self.update_footer()
	
	def get_selected(self):
		
		return self.classlist.get_selected()
	
	def update_footer(self):
		
		selected = self.get_selected()
		enabled = (len(selected) == 1) and (selected[0] != "!*")
		
		self.footer.set_rename_enabled(enabled)
		self.footer.set_order_up_enabled(enabled)
		self.footer.set_order_down_enabled(enabled)
		self.footer.set_remove_enabled((len([name for name in selected if name != "!*"]) > 0))
	
	def change_order(self, dir):
		
		name = self.get_selected()[0]
		parent = self.classlist.get_selected_parent()
		if parent is None:
			names = [name for name in self.model.class_names if not name in self.model.descriptor_names]
		else:
			names = self.model.classes[parent].descriptors
		
		if len(names) == 1:
			return
		idx = names.index(name)
		if (dir == -1) and (idx == 0):
			return
		if (dir == 1) and (idx == len(names) - 1):
			return
		
		self.model.classes.switch_order(name, names[idx + dir])

	def order_up(self):
		
		self.change_order(-1)
	
	def order_down(self):
		
		self.change_order(1)
	
	def add(self):
		
		self.view.dialogs.open("AddClass")
	
	def rename(self):

		self.view.dialogs.open("RenameClass", self.get_selected()[0])
	
	def remove(self):
		
		self.view.dialogs.open("RemoveClass", [name for name in self.get_selected() if name != "!*"])
	
	def on_view_action(self, args):

		self.update_footer()

class ClassFooter(DModule, QtWidgets.QFrame):
	
	def __init__(self, parent):

		self.parent = parent

		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self)

		self.set_up()

	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(6)
		self.setLayout(self.layout)
		
		self.button_up = QtWidgets.QToolButton(self)
		self.button_up.setIcon(self.parent.view.get_icon("up_small.svg"))
		self.button_up.setIconSize(QtCore.QSize(32, 32))
		self.button_up.setToolTip("Order Class Up")
		self.button_up.clicked.connect(self.on_up)
		self.layout.addWidget(self.button_up)
		
		self.button_down = QtWidgets.QToolButton(self)
		self.button_down.setIcon(self.parent.view.get_icon("down_small.svg"))
		self.button_down.setIconSize(QtCore.QSize(32, 32))
		self.button_down.setToolTip("Order Class Down")
		self.button_down.clicked.connect(self.on_down)
		self.layout.addWidget(self.button_down)
		
		self.layout.addStretch()
		
		self.button_add = QtWidgets.QToolButton(self)
		self.button_add.setIcon(self.parent.view.get_icon("add_class.svg"))
		self.button_add.setIconSize(QtCore.QSize(32, 32))
		self.button_add.setToolTip("Add Class")
		self.button_add.clicked.connect(self.on_add)
		self.layout.addWidget(self.button_add)
		
		self.button_rename = QtWidgets.QToolButton(self)
		self.button_rename.setIcon(self.parent.view.get_icon("edit_class.svg"))
		self.button_rename.setIconSize(QtCore.QSize(32, 32))
		self.button_rename.setToolTip("Rename Class")
		self.button_rename.clicked.connect(self.on_rename)
		self.layout.addWidget(self.button_rename)
		
		self.button_remove = QtWidgets.QToolButton(self)
		self.button_remove.setIcon(self.parent.view.get_icon("remove_class.svg"))
		self.button_remove.setIconSize(QtCore.QSize(32, 32))
		self.button_remove.setToolTip("Remove Class")
		self.button_remove.clicked.connect(self.on_remove)
		self.layout.addWidget(self.button_remove)
	
	def set_order_up_enabled(self, state):
		
		self.button_up.setEnabled(state)
	
	def set_order_down_enabled(self, state):
		
		self.button_down.setEnabled(state)
	
	def set_rename_enabled(self, state):
		
		self.button_rename.setEnabled(state)
	
	def set_remove_enabled(self, state):
		
		self.button_remove.setEnabled(state)
	
	def on_up(self, *args):
		
		self.parent.order_up()
	
	def on_down(self, *args):
		
		self.parent.order_down()
	
	def on_add(self, *args):
		
		self.parent.add()
	
	def on_rename(self, *args):
		
		self.parent.rename()
	
	def on_remove(self, *args):
		
		self.parent.remove()
