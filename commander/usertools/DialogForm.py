from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools.DialogColumn import (DialogColumn)
from deposit.commander.usertools.DialogFrame import (DialogFrame)
from deposit.commander.usertools.DialogGroup import (DialogGroup)
from deposit.commander.usertools.DialogMultiGroup import (DialogMultiGroup)
from deposit.commander.usertools.UserGroups import (Group, MultiGroup)
from deposit.commander.usertools.UserControls import (UserControl, Select)
from deposit.commander.usertools.ColumnBreak import (ColumnBreak)
from deposit.commander.usertools.VerticalScrollArea import (VerticalScrollArea)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class DialogForm(ViewChild, QtWidgets.QDialog):

	def __init__(self, model, view, form_tool):
		
		self.form_tool = form_tool
		self.buttonBox = None
		self.columns = []  # [DialogColumn(), ...]
		self.selects = []  # [[class, descriptor], ...]
		
		ViewChild.__init__(self, model, view)
		QtWidgets.QDialog.__init__(self, self.view)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		
		self.setWindowTitle(self.form_tool.label)
		self.setMinimumWidth(256)
		self.setModal(False)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.layout().setContentsMargins(0, 0, 0, 0)
		
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QHBoxLayout())
		self.controls_frame.layout().setContentsMargins(10, 10, 10, 10)
		
		self.scroll_area = VerticalScrollArea(self.controls_frame)
		
		self.layout().addWidget(self.scroll_area)
		
		self.button_frame = QtWidgets.QFrame()
		self.button_frame.setLayout(QtWidgets.QHBoxLayout())
		self.button_frame.layout().setContentsMargins(5, 5, 5, 5)
		self.button_frame.layout().addStretch()
		button_submit = QtWidgets.QPushButton("Submit")
		button_submit.clicked.connect(self.on_submit)
		self.button_frame.layout().addWidget(button_submit)
		button_reset = QtWidgets.QPushButton("Reset")
		button_reset.clicked.connect(self.on_reset)
		self.button_frame.layout().addWidget(button_reset)
		self.layout().addWidget(self.button_frame)
		
		for element in self.form_tool.elements:
			if issubclass(element.__class__, Select):
				self.add_select(element)
			elif isinstance(element, ColumnBreak):
				self.add_column()
			elif issubclass(element.__class__, UserControl):
				self.add_frame(element)
			elif issubclass(element.__class__, Group):
				self.add_group(element)
		
		self.adjust_labels()
		
		pass
	
	def set_enabled(self, state):
		
		if self.buttonBox is not None:
			self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(state)
	
	def add_column(self):
		
		self.columns.append(DialogColumn())
		self.controls_frame.layout().addWidget(self.columns[-1])
	
	def add_frame(self, user_control):
		
		self.columns[-1].add_widget(DialogFrame(self.model, user_control))
	
	def add_group(self, user_group):
		
		dialog_group = None
		if isinstance(user_group, MultiGroup):
			dialog_group = DialogMultiGroup(self.model, user_group)
		elif isinstance(user_group, Group):
			dialog_group = DialogGroup(self.model, user_group)
		if dialog_group is None:
			return
		self.columns[-1].add_widget(dialog_group)
	
	def add_select(self, user_select):
	
		self.selects.append([user_select.dclass, user_select.descriptor])
	
	def multigroups(self):
		# returns [DialogMultiGroup(), ...]
		
		groups = []
		for column in self.columns:
			for group in column.findChildren(DialogMultiGroup, options = QtCore.Qt.FindDirectChildrenOnly):
				groups.append(group)
		return groups
	
	def frames(self):
		# returns frames, framesets
		# frames = [DialogFrame(), ...]
		# framesets = [[DialogFrame(), ...], ...]
		
		frames, framesets = [], []
		for column in self.columns:
			for element in column.findChildren(QtWidgets.QWidget, options = QtCore.Qt.FindDirectChildrenOnly):
				if isinstance(element, DialogGroup):
					frames += element.frames()
				elif isinstance(element, DialogMultiGroup):
					framesets += element.framesets()
				elif isinstance(element, DialogFrame):
					frames.append(element)
		return frames, framesets
	
	def adjust_labels(self):
		
		for column in self.columns:
			wmax = 0
			for label in column.findChildren(QtWidgets.QLabel):
				wmax = max(wmax, label.sizeHint().width())
			for label in column.findChildren(QtWidgets.QLabel):
				label.setFixedWidth(wmax)
				label.setAlignment(QtCore.Qt.AlignRight)
			
	def sizeHint(self):
		
		w = self.controls_frame.sizeHint().width()
		h = self.controls_frame.sizeHint().height() + self.button_frame.sizeHint().height()
		return QtCore.QSize(w, h)
	
	def on_submit(self, *args):
		
		pass
	
	def on_reset(self, *args):
		
		pass

