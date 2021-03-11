from deposit.commander.usertools.DialogFrame import (DialogFrame)

from PySide2 import (QtWidgets, QtCore, QtGui)
from natsort import (natsorted)

class DialogGroup(QtWidgets.QGroupBox):
	
	entry_removed = QtCore.Signal(list) # [obj_id, ...]
	
	def __init__(self, model, user_group):
		# user_group = Group
		
		self.model = model
		self.user_group = user_group
		self.controls_frame = None
		
		QtWidgets.QGroupBox.__init__(self, self.user_group.label)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.controls_frame = QtWidgets.QFrame()
		self.controls_frame.setLayout(QtWidgets.QVBoxLayout())
		self.controls_frame.layout().setContentsMargins(10, 10, 10, 10)
		self.layout().addWidget(self.controls_frame)
		
		self.lookup_combo = LookupCombo()
		self.lookup_combo_search = {} # {index: {column: value, ...}}
		lookup_button = QtWidgets.QPushButton("Fill")
		lookup_button.clicked.connect(self.on_lookup_combo)
		
		lookup_frame = QtWidgets.QFrame()
		lookup_frame.setLayout(QtWidgets.QHBoxLayout())
		lookup_frame.layout().addStretch()
		lookup_frame.layout().addWidget(self.lookup_combo)
		lookup_frame.layout().addWidget(lookup_button)
		self.controls_frame.layout().addWidget(lookup_frame)
		
		for member in self.user_group.members:
			self.add_frame(member)
		
		button_frame = QtWidgets.QWidget()
		button_frame.setLayout(QtWidgets.QHBoxLayout())
		button_remove = QtWidgets.QPushButton("Remove")
		button_remove.clicked.connect(self.on_remove)
		button_frame.layout().addStretch()
		button_frame.layout().addWidget(button_remove)
		self.controls_frame.layout().addWidget(button_frame)
		
		self.populate_lookup()
		
		self.setStyleSheet(self.user_group.stylesheet)
	
	def add_frame(self, user_control):
		
		frame = DialogFrame(self.model, user_control)
		frame.ctrl.changed.connect(self.on_ctrl_changed)
		self.controls_frame.layout().addWidget(frame)
	
	def populate_lookup(self):
		
		self.lookup_combo.clear()
		self.lookup_combo_search = {} # {index: {column: value, ...}}
		columns = [".".join([member.dclass, member.descriptor]) for member in self.user_group.members]
		query = self.model.query("SELECT %s" % (", ".join(columns)))
		rows = []
		for row in query:
			data = dict([(column, str(row[column])) for column in columns])
			label = ", ".join([data[column] for column in columns])
			row = [label, data]
			if row not in rows:
				rows.append(row)
		rows = natsorted(rows, key = lambda row: row[0])
		index = 0
		for label, data in rows:
			self.lookup_combo_search[index] = data
			index += 1
			self.lookup_combo.addItem(label, data)
	
	def remove(self):
		
		obj_ids = set([])
		for frame in self.frames():
			obj_id = frame.ctrl.obj_id
			if obj_id is not None:
				obj_ids.add(obj_id)
			frame.set_value("", None)
		return list(obj_ids)
	
	def set_data(self, data):
		# data = {Class.Descriptor: value, ...}
		
		for frame in self.frames():
			column = ".".join([frame.user_control.dclass, frame.user_control.descriptor])
			if column in data:
				frame.set_value(data[column])
	
	def update_lookup_combo(self):
		
		def _find_index(data):
			
			for index in self.lookup_combo_search:
				found = True
				for column in data:
					if column not in self.lookup_combo_search[index]:
						found = False
						break
					if self.lookup_combo_search[index][column] != data[column]:
						found = False
						break
				if found:
					return index
			return None
		
		data = {}
		for frame in self.frames():
			value = frame.get_value()
			if value != "":
				column = ".".join([frame.user_control.dclass, frame.user_control.descriptor])
				data[column] = value
		if not data:
			return
		index = _find_index(data)
		if index is None:
			return
		self.lookup_combo.setCurrentIndex(index)
	
	def frames(self):
		
		return list(self.controls_frame.findChildren(DialogFrame, options = QtCore.Qt.FindDirectChildrenOnly))
	
	def on_ctrl_changed(self):
		
		self.update_lookup_combo()
	
	def on_lookup_combo(self):
		
		data = self.lookup_combo.currentData()
		if data is None:
			return
		self.set_data(data)
	
	def on_remove(self, *args):
		
		obj_ids = self.remove()
		self.entry_removed.emit(obj_ids)

class LookupCombo(QtWidgets.QComboBox):
	
	def wheelEvent(self, event):
		
		pass

