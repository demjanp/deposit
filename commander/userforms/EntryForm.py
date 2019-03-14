from deposit import Broadcasts
from deposit.commander.userforms._Form import (Form)

from PyQt5 import (QtWidgets, QtCore, QtGui)
from collections import defaultdict

class EntryForm(Form):
	
	def set_up(self, elements):
		
		# self.controls = {class.descriptor: QWidget, group_frame_nr: {class.descriptor: QWidget, ...}, ...}
		
		self.max_group_frame_nr = 1
		
		self.central_frame.setLayout(QtWidgets.QHBoxLayout())
		self.central_frame.layout().setContentsMargins(0, 0, 0, 0)
		column = self.add_column()
		for element in elements[2:]:
			# element = [tag, group, multigroup, ...]
			# tag = [control type, select, label]
			# select = "class.descriptor"
			# group = [["Group", title], tag, ...], multigroup = [["MultiGroup", title], tag, ...]
			if element[0] == "ColumnBreak":
				column = self.add_column()
			elif isinstance(element[0], list): # group or multigroup
				typ, title = element[0]
				if typ == "Group":
					group = self.add_group(column, title)
					group._tags = element[1:].copy()
				elif typ == "MultiGroup":
					group = self.add_multi_group(column, title)
					group._tags = element[1:].copy()
				else:
					continue
				frame = self.add_frame(group)
				frame._group_frame_nr = self.max_group_frame_nr
				for tag in element[1:]:
					self.add_row(frame, tag, group_frame_nr = self.max_group_frame_nr)
				self.max_group_frame_nr += 1
			else: # tag
				frame = self.add_frame(column)
				frame._select = element[1]
				self.add_row(frame, element)
		
		self.update_controls()
	
	def add_column(self):
		
		column = QtWidgets.QFrame()
		column.setLayout(QtWidgets.QVBoxLayout())
		column.layout().setContentsMargins(0, 0, 0, 0)
		column.layout().addStretch()
		self.central_frame.layout().addWidget(column)
		return column
	
	def add_group(self, column, title):
		
		group = QtWidgets.QGroupBox(title)
		group._multi = False
		group.setLayout(QtWidgets.QVBoxLayout())
		group.layout().setContentsMargins(0, 0, 0, 0)
		column.layout().insertWidget(column.layout().count() - 1, group)
		return group
	
	def add_multi_group(self, column, title):
		
		group = self.add_group(column, title)
		group._multi = True
		button_frame = QtWidgets.QFrame()
		button_frame.setLayout(QtWidgets.QHBoxLayout())
		button_frame.layout().setContentsMargins(0, 0, 0, 0)
		button_frame.layout().addStretch()
		button = QtWidgets.QPushButton("Add Entry")
		button._group = group
		button.clicked.connect(self.on_add_entry)
		button_frame.layout().addWidget(button)
		group.layout().addWidget(button_frame)
		return group
	
	def add_frame(self, parent):
		
		frame = QtWidgets.QFrame()
		frame.setLayout(QtWidgets.QFormLayout())
		frame.layout().setContentsMargins(10, 10, 10, 10)
		if isinstance(parent, QtWidgets.QGroupBox):
			if parent._multi:
				if parent.layout().count() > 1:
					line = QtWidgets.QFrame(parent)
					line.setFrameShape(QtWidgets.QFrame.HLine)
					line.setFrameShadow(QtWidgets.QFrame.Sunken)
					line._line = True
					parent.layout().insertWidget(parent.layout().count() - 1, line)
				parent.layout().insertWidget(parent.layout().count() - 1, frame)
			else:
				parent.layout().addWidget(frame)
		else:
			parent.layout().insertWidget(parent.layout().count() - 1, frame)
		return frame
	
	def add_row(self, frame, element, value = None, group_frame_nr = None):
		
		label, ctrl, select = self.make_row(element)
		if label is None:
			return
		if group_frame_nr is None:
			self.controls[select] = ctrl
			frame.layout().addRow(label, self.controls[select])
		else:
			if group_frame_nr not in self.controls:
				self.controls[group_frame_nr] = {}
			self.controls[group_frame_nr][select] = ctrl
			frame.layout().addRow(label, self.controls[group_frame_nr][select])
		self.set_control(select, value, group_frame_nr)
	
	def add_group_frame(self, group, values = {}):
		# values = {select: value, ...}
		
		frame = self.add_frame(group)
		frame._group_frame_nr = self.max_group_frame_nr
		for tag in group._tags:
			value = None
			if tag[1] in values:
				value = values[tag[1]]
			self.add_row(frame, tag, value, group_frame_nr = self.max_group_frame_nr)
		self.max_group_frame_nr += 1
	
	def clear_group_frame(self, group):
		
		for frame in group.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
			if frame.__class__.__name__ != "QFrame":
				continue
			if group._multi:
				if hasattr(frame, "_group_frame_nr"):
					del self.controls[frame._group_frame_nr]
				if hasattr(frame, "_group_frame_nr") or hasattr(frame, "_line"):
					group.layout().removeWidget(frame)
					frame.setParent(None)
			else:
				for _, select, _ in group._tags:
					self.set_control(select, None, frame._group_frame_nr)
	
	def find_relations(self):
		# find all possible relations
		# returns [[cls1, rel, cls2], ...]
		
		relations = []
		classes = set()
		for key in self.controls:
			if isinstance(key, int):
				for select in self.controls[key]:
					classes.add(select.split(".")[0])
			else:
				classes.add(key.split(".")[0])
		for cls1 in classes:
			for rel in self.model.classes[cls1].relations:
				if rel[0] == "~":
					continue
				for cls2 in self.model.classes[cls1].relations[rel]:
					if cls2 in classes:
						relations.append([cls1, rel, cls2])
		return relations
	
	def get_selected(self):
		
		current = self.view.mdiarea.get_current()
		if current and hasattr(current, "get_selected_objects"):
			objects = list(current.get_selected_objects().values())
			if len(objects) == 1:
				return objects[0].id
		return None
	
	def reset_controls(self, add_empty_groups = False):
		
		for column in self.central_frame.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
			for frame in column.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
				if hasattr(frame, "_select"):
					self.set_control(frame._select, None)
			for group in column.findChildren(QtWidgets.QGroupBox, options = QtCore.Qt.FindDirectChildrenOnly):
				self.clear_group_frame(group)
				if add_empty_groups and group._multi:
					self.add_group_frame(group)
	
	def update_controls(self):
		
		selected_id = self.get_selected()
		if selected_id is None:
			return
		
		self.reset_controls()
		
		# find all possible relations
		relations = self.find_relations() # [[cls1, rel, cls2], ...]
		collect = []
		for cls1, rel, cls2 in relations:
			rel_rev = self.model.reverse_relation(rel)
			collect.append([cls2, rel_rev, cls1])
		relations += collect
		
		# find classes from multi entry fields
		multi_classes = defaultdict(set) # {cls: set(group, ...), ...}
		for column in self.central_frame.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
			for group in column.findChildren(QtWidgets.QGroupBox, options = QtCore.Qt.FindDirectChildrenOnly):
				if not group._multi:
					continue
				for _, select, _ in group._tags:
					multi_classes[select.split(".")[0]].add(group)
		
		# get all relevant objects
		objects = defaultdict(list)  # {class: [object, ...], ...}
		obj = self.model.objects[selected_id]
		for cls in obj.classes:
			objects[cls].append(obj)
		while True:
			found = False
			for cls1, rel, cls2 in relations:
				if cls1 in objects:
					for obj1 in objects[cls1]:
						if rel in obj1.relations:
							for obj_id2 in obj1.relations[rel]:
								obj2 = self.model.objects[obj_id2]
								if (cls2 in obj2.classes) and ((cls2 in multi_classes) or (cls2 not in objects)) and (obj2 not in objects[cls2]):
									objects[cls2].append(obj2)
									found = True
			if not found:
				break
		
		# collect data from objects
		data = {}  # {cls: {obj_id: {descr: value, ...}, ...}, ...}
		for cls in objects:
			data[cls] = {}
			for obj in objects[cls]:
				data[cls][obj.id] = {}			
				for descr in obj.descriptors:
					value = obj.descriptors[descr].label.value
					if value is None:
						continue
					data[cls][obj.id][descr] = value
		
		# fill single entry fields
		for select in self.controls:
			if isinstance(select, int):
				continue
			cls, descr = select.split(".")
			if cls not in data:
				continue
			obj_id = next(iter(data[cls]))
			if descr in data[cls][obj_id]:
				self.set_control(select, data[cls][obj_id][descr])
		
		# fill multi entry fields
		group_values = defaultdict(dict)  # {obj_id: {select: value, ...}, ...}
		group_ids = defaultdict(set)  # {obj_id: set(group, ...), ...}
		for cls in data:
			if cls not in multi_classes:
				continue
			for obj_id in data[cls]:
				for group in multi_classes[cls]:
					group_ids[obj_id].add(group)
				for descr in data[cls][obj_id]:
					group_values[obj_id]["%s.%s" % (cls, descr)] = data[cls][obj_id][descr]
		for obj_id in group_values:
			for group in group_ids[obj_id]:
				self.add_group_frame(group, group_values[obj_id])
	
	def submit(self):
		
		# find all possible relations
		relations = self.find_relations() # [[cls1, rel, cls2], ...]
		
		# find multi entry frames
		multi_frames = set()
		for column in self.central_frame.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
			for group in column.findChildren(QtWidgets.QGroupBox, options = QtCore.Qt.FindDirectChildrenOnly):
				if group._multi:
					for frame in group.findChildren(QtWidgets.QFrame, options = QtCore.Qt.FindDirectChildrenOnly):
						if hasattr(frame, "_group_frame_nr"):
							multi_frames.add(frame._group_frame_nr)
		
		# collect values from form
		values = defaultdict(lambda: defaultdict(dict)) # {cls: {idx: {descr: value, ...}, ...}, ...}
		for key in self.controls:
			if isinstance(key, int):
				for select in self.controls[key]:
					value = self.get_value(select, key)
					cls, descr = select.split(".")
					if key in multi_frames:
						values[cls][key][descr] = value
					else:
						values[cls][0][descr] = value
			else:
				value = self.get_value(key)
				cls, descr = key.split(".")
				values[cls][0][descr] = value
		
		# create / find objects
		objects = defaultdict(dict) # {cls: {idx: obj_id, ...}, ...}
		for cls in values:
			for idx in values[cls]:
				if not (True in [(value is not None) for value in values[cls][idx].values()]):
					continue
				found = False
				for id in self.model.classes[cls].objects:
					obj = self.model.objects[id]
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
					objects[cls][idx] = self.model.classes.add(cls).objects.add().id
					for descr in values[cls][idx]:
						value = values[cls][idx][descr]
						if value is None:
							continue
						self.model.objects[objects[cls][idx]].descriptors.add(descr, value)
		
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
					self.model.objects[obj_id1].relations.add(rel, obj_id2)
	
	@QtCore.pyqtSlot()
	def on_add_entry(self):
		
		self.add_group_frame(self.sender()._group)
	
	def on_reset(self, *args):
		
		self.reset_controls(add_empty_groups = True)
	
	def on_submit(self, *args):
		
		self.submit()
		self.reset_controls(add_empty_groups = True)

