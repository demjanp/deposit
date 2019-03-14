from deposit.DModule import (DModule)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class Form(DModule, QtWidgets.QDialog):
	
	def __init__(self, model, view, elements):
		
		self.model = model
		self.view = view
		self.buttonBox = None
		self.controls = {}  # {class.descriptor: QWidget, group_frame_nr: {class.descriptor: QWidget, ...}, ...}
		
		DModule.__init__(self)
		QtWidgets.QDialog.__init__(self, self.view)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		
		self.setWindowTitle(elements[0][1])
		self.setMinimumWidth(256)
		self.setModal(False)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.central_frame = QtWidgets.QFrame()
		self.layout().addWidget(self.central_frame)
		
		button_frame = QtWidgets.QFrame()
		button_frame.setLayout(QtWidgets.QHBoxLayout())
		button_frame.layout().setContentsMargins(0, 0, 0, 0)
		button_frame.layout().addStretch()
		button_submit = QtWidgets.QPushButton("Submit")
		button_submit.clicked.connect(self.on_submit)
		button_frame.layout().addWidget(button_submit)
		button_reset = QtWidgets.QPushButton("Reset")
		button_reset.clicked.connect(self.on_reset)
		button_frame.layout().addWidget(button_reset)
		self.layout().addWidget(button_frame)
		
		self.set_up(elements)
		
		self.adjustSize()

	def set_enabled(self, state):

		if self.buttonBox is not None:
			self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(state)
	
	def make_control(self, name):
		# returns QWidget
		
		name = "Q%s" % name
		if not hasattr(QtWidgets, name):
			return None
		ctrl = getattr(QtWidgets, name)()
		if name == "QComboBox":
			ctrl.setEditable(True)
		return ctrl
	
	def make_row(self, element):
		
		bold = False
		if len(element) == 4:
			if element[2] == "bold":
				bold = True
				element = element[:2] + [element[3]]
			else:
				return None, None, None
		ctrl, select, label = element
		ctrl = self.make_control(ctrl)
		if ctrl is None:
			return None, None, None
		ctrl._select = select
		label = QtWidgets.QLabel("%s:" % label)
		
		return label, ctrl, select
	
	def get_control(self, select, group_frame_nr = None):
		
		ctrl = None
		if group_frame_nr is not None:
			if (group_frame_nr not in self.controls) or (select not in self.controls[group_frame_nr]):
				return None
			return self.controls[group_frame_nr][select]
		if select not in self.controls:
			return None
		return self.controls[select]
	
	def get_value(self, select, group_frame_nr = None):
		
		value = ""
		ctrl = self.get_control(select, group_frame_nr)
		if ctrl is None:
			return value
		if isinstance(ctrl, QtWidgets.QLineEdit):
			value = ctrl.text()
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			value = ctrl.toPlainText()
		elif isinstance(ctrl, QtWidgets.QComboBox):
			value = ctrl.currentText()
		elif isinstance(ctrl, QtWidgets.QCheckBox):
			value = str(int(ctrl.isChecked()))
		return value.strip()
	
	def update_combo(self, select, set_value = None, group_frame_nr = None):
		
		ctrl = self.get_control(select, group_frame_nr)
		if ctrl is None:
			return
		cls, descr = select.split(".")
		ctrl.clear()
		values = set()
		for id in self.model.classes[cls].objects:
			value = self.model.objects[id].descriptors[descr].label.value
			if value is not None:
				values.add(value)
		values = sorted(list(values))
		if values:
			ctrl.addItems([""] + values)
		if set_value is not None:
			set_value = str(set_value)
			if set_value in values:
				ctrl.setCurrentIndex(values.index(set_value) + 1)
			elif values:
				ctrl.setItemText(0, set_value)
			else:
				ctrl.setCurrentText(set_value)
	
	def set_control(self, select, value, group_frame_nr = None):
		
		ctrl = self.get_control(select, group_frame_nr)
		if ctrl is None:
			return
		if value is None:
			value = ""
		if isinstance(ctrl, QtWidgets.QLineEdit):
			ctrl.setText(value)
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			ctrl.setPlainText(value)
		elif isinstance(ctrl, QtWidgets.QComboBox):
			self.update_combo(select, value, group_frame_nr)
		elif isinstance(ctrl, QtWidgets.QCheckBox):
			try:
				value = bool(int(value))
			except:
				value = False
			ctrl.setChecked(value)
	
	def set_up(self, elements):
		
		pass
	
	def on_submit(self, *args):
		
		pass
	
	def on_reset(self, *args):
		
		pass

