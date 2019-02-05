from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
from collections import defaultdict
import os

class View(*uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "View.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.plugins.C14FormMembers.ui")):
	
	def __init__(self, parent):

		self.parent = parent
		# model = self.parent.parent.model
		# view = self.parent.parent.view

		QtWidgets.QMainWindow.__init__(self)
		self.setupUi(self)

		self.store = self.parent.parent.model
		self.targets = [] # [[control, class, descriptor], ...]
		self.multi_entry = {} # {group_key: [[control_class, label, class, descriptor], ...], ...}
		
		self.set_up()
	
	def set_up(self):
		
		# get control targets
		self.targets = []
		for key in self.__dict__:
			ctrl = self.__dict__[key]
			value = self.get_control_value(ctrl)
			if value == "":
				continue
			self.clear_control(ctrl)
			value = value.split(".")
			if len(value) != 2:
				continue
			self.targets.append([ctrl] + value)
		
		# get multi-entry groups
		self.multi_entry = {}
		for key in self.__dict__:
			ctrl = self.__dict__[key]
			
			# check if control is a multi-entry group
			if not isinstance(ctrl, QtWidgets.QGroupBox):
				continue
			button = ctrl.findChildren(QtWidgets.QPushButton)
			if len(button) != 1:
				continue
			button = button[0]
			
			# bind button action
			button._group = key
			button.clicked.connect(self.on_add_entry)
			
			# store control information
			self.multi_entry[key] = []
			for ctrl in ctrl.findChildren(QtWidgets.QFrame):
				break
			ctrl._multi = 0
			for row in range(ctrl.layout().rowCount()):
				label = ctrl.layout().itemAt(row, QtWidgets.QFormLayout.LabelRole).widget().text()
				field = ctrl.layout().itemAt(row, QtWidgets.QFormLayout.FieldRole).widget()
				field._multi = 0
				cls, descr = self.get_control_class_descr(field)
				if cls is None:
					continue
				self.multi_entry[key].append([field.__class__, label, cls, descr])
				
	def get_control_class_descr(self, ctrl):
		
		for ctrl2, cls, descr in self.targets:
			if ctrl2 == ctrl:
				return cls, descr
		return None, None
	
	def clear_control(self, ctrl):
		
		if isinstance(ctrl, QtWidgets.QComboBox):
			ctrl.clear()
		elif isinstance(ctrl, QtWidgets.QLineEdit):
			ctrl.setText("")
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			ctrl.setPlainText("")
	
	def get_control_value(self, ctrl):
		
		value = ""
		if isinstance(ctrl, QtWidgets.QComboBox):
			value = ctrl.currentText()
		elif isinstance(ctrl, QtWidgets.QLineEdit):
			value = ctrl.text()
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			value = ctrl.toPlainText()
		return value.strip()
	
	def reset_controls(self):
		
		# remove excess entries from multi-entry groups
		for key in self.multi_entry:
			ctrl = self.__dict__[key]
			for ctrl2 in ctrl.findChildren(QtWidgets.QFrame):
				if hasattr(ctrl2, "_multi") and (ctrl2._multi > 0):
					children = list(ctrl2.findChildren(QtWidgets.QWidget))
					self.targets = [row for row in self.targets if (row[0] not in children)]
					ctrl.layout().removeWidget(ctrl2)
					ctrl2.setParent(None)
		
		# clear controls
		for ctrl, _, _ in self.targets:
			self.clear_control(ctrl)
		
		# update controls with values according to targets
		for ctrl, cls, descr in self.targets:
			if isinstance(ctrl, QtWidgets.QComboBox):
				self.update_combo(ctrl)
	
	def update_combo(self, ctrl):
		
		cls, descr = self.get_control_class_descr(ctrl)
		if cls is None:
			return
		ctrl.clear()
		values = []
		for id in self.store.classes[cls].objects:
			value = self.store.objects[id].descriptors[descr].label.value
			if (value is not None) and (value not in values):
				values.append(value)
		if values:
			ctrl.addItems([""] + values)
	
	def add_group_entry(self, key):
		
		group_ctrl = self.__dict__[key]
		
		multi_last = 0
		for frame in group_ctrl.findChildren(QtWidgets.QFrame):
			if hasattr(frame, "_multi"):
				multi_last = max(multi_last, frame._multi)
		
		frame = QtWidgets.QFrame(group_ctrl)
		frame.setLayout(QtWidgets.QFormLayout())
		frame.setStyleSheet("font-weight: normal;")
		frame.layout().setContentsMargins(0, 0, 0, 0)
		frame._multi = multi_last + 1
		
		line = QtWidgets.QFrame(group_ctrl)
		line.setFrameShape(QtWidgets.QFrame.HLine)
		line.setFrameShadow(QtWidgets.QFrame.Sunken)
		line._multi = multi_last + 1
		
		group_ctrl.layout().insertWidget(group_ctrl.layout().count() - 1, line)
		group_ctrl.layout().insertWidget(group_ctrl.layout().count() - 1, frame)
		
		added = []
		for control_cls, label, cls, descr in self.multi_entry[key]:
			label = QtWidgets.QLabel(label)
			field = control_cls()
			if control_cls == QtWidgets.QComboBox:
				field.setEditable(True)
			label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			field._multi = multi_last + 1
			frame.layout().addRow(label, field)
			frame.adjustSize()
			self.targets.append([field, cls, descr])
			added.append(field)
			if isinstance(field, QtWidgets.QComboBox):
				self.update_combo(field)
		return added
	
	def submit(self):
		
		# find all possible relations
		relations = [] # [[cls1, rel, cls2], ...]
		classes = []
		for _, cls, _ in self.targets:
			if cls not in classes:
				classes.append(cls)
		for cls1 in classes:
			for rel in self.store.classes[cls1].relations:
				if rel[0] == "~":
					continue
				for cls2 in self.store.classes[cls1].relations[rel]:
					if cls2 in classes:
						relations.append([cls1, rel, cls2])
		
		# collect values from form
		values = defaultdict(lambda: defaultdict(dict)) # {cls: {idx: {descr: value, ...}, ...}, ...}
		for ctrl, cls, descr in self.targets:
			value = self.get_control_value(ctrl)
			if value == "":
				value = None
			idx = ctrl._multi if hasattr(ctrl, "_multi") else 0
			values[cls][idx][descr] = value
		
		# create / find objects
		objects = defaultdict(dict) # {cls: {idx: obj_id, ...}, ...}
		for cls in values:
			for idx in values[cls]:
				if not (True in [(value is not None) for value in values[cls][idx].values()]):
					continue
				found = False
				for id in self.store.classes[cls].objects:
					obj = self.store.objects[id]
					found = True
					for descr in values[cls][idx]:
						if obj.descriptors[descr].label.value != values[cls][idx][descr]:
							found = False
							break
					if found:
						break
				if found:
					objects[cls][idx] = id
				else:
					objects[cls][idx] = self.store.classes.add(cls).objects.add().id
					for descr in values[cls][idx]:
						value = values[cls][idx][descr]
						if value is None:
							continue
						self.store.objects[objects[cls][idx]].descriptors.add(descr, value)
		
		# create relations
		for cls1, rel, cls2 in relations:
			if not ((cls1 in objects) and (cls2 in objects)):
				continue
			for idx1 in objects[cls1]:
				obj_id1 = objects[cls1][idx1]
				for idx2 in objects[cls2]:
					obj_id2 = objects[cls2][idx2]
					if obj_id1 == obj_id2:
						continue
					self.store.objects[obj_id1].relations.add(rel, obj_id2)
	
	def on_activate(self):
		
		self.reset_controls()
	
	@QtCore.pyqtSlot()
	def on_add_entry(self):
		
		self.add_group_entry(self.sender()._group)
	
	@QtCore.pyqtSlot()
	def on_resetButton_clicked(self):
		
		self.reset_controls()
	
	@QtCore.pyqtSlot()
	def on_submitButton_clicked(self):
		
		self.submit()
		self.reset_controls()
	
