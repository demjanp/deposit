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

		self._queries = {}  # {key: [[cls1, descr, rel, cls2, unique], ...], ...}; cls2 = class or "{primary}"
		self._groups = {} # {key: [[label, field Qt class, descriptor name, unique], ...]
		self._obj_lookup = defaultdict(list) # {"selected" or Class: [obj_id, ...], ...}
		self._key_order = [] # [key, ...]
		self._edited = [] # [key, ...]
		
		self.store = self.parent.parent.model
		
		self._edit_timer = QtCore.QTimer()
		self._edit_timer.setSingleShot(True)
		self._edit_timer.timeout.connect(self.on_edit_timer)
		self._edit_sender = None
		
		self.register_controls()
		self.update_controls()

	def clear_control(self, key):
		
		if isinstance(key, str):
			ctrl = self.__dict__[key]
		else:
			ctrl = key
		if hasattr(ctrl, "blockSignals"):
			ctrl.blockSignals(True)
		if isinstance(ctrl, QtWidgets.QGroupBox):
			for frame in ctrl.findChildren(QtWidgets.QFrame):
				frame.setParent(None)
		elif isinstance(ctrl, QtWidgets.QComboBox):
			ctrl.clear()
		elif isinstance(ctrl, QtWidgets.QLineEdit):
			ctrl.setText("")
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			ctrl.setPlainText("")
		if hasattr(ctrl, "blockSignals"):
			ctrl.blockSignals(False)
	
	def get_control_value(self, key):
		
		value = ""
		if isinstance(key, str):
			ctrl = self.__dict__[key]
		else:
			ctrl = key
		if isinstance(ctrl, QtWidgets.QComboBox):
			value = ctrl.currentText()
		elif isinstance(ctrl, QtWidgets.QLineEdit):
			value = ctrl.text()
		elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
			value = ctrl.toPlainText()
		return value.strip()
	
	def bind_control(self, ctrl):
		
		if isinstance(ctrl, QtWidgets.QComboBox):
			ctrl.editTextChanged.connect(self.on_edit)
		elif isinstance(ctrl, QtWidgets.QLineEdit):
			ctrl.textChanged.connect(self.on_edit)
	
	def register_controls(self):
		
		def parse_query(querystr):
			
			res = []
			unique = False
			querystr = querystr.strip()
			if querystr.endswith("{unique}"):
				unique = True
				querystr = querystr[:-8].strip()
			for query in querystr.split(";"):
				query = query.strip().split(" ")
				if len(query) == 2:
					if "." in query[0]:
						cls1, descr = query[0].split(".")
					else:
						cls1, descr = query[0], None
					if query[1] == "{primary}":
						rel, cls2 = None, "{primary}"
					else:
						rel, cls2 = query[1].split(".")
					if rel is not None:
						rel = self.store.reverse_relation(rel)
					res.append([cls1, descr, rel, cls2, unique])
			return res
		
		for key in self.__dict__:
			ctrl = self.__dict__[key]
			if isinstance(ctrl, QtWidgets.QGroupBox):
				title = ctrl.title()
				if "@" in title:
					idx = title.find("@")
					title, queries = title[:idx], parse_query(title[idx + 1:])
					if queries:
						self._queries[key] = queries
						ctrl.setTitle(title)
						self._groups[key] = []
						for frame in ctrl.findChildren(QtWidgets.QFrame):
							layout = frame.layout()
							if isinstance(layout, QtWidgets.QFormLayout):
								for i in reversed(range(layout.rowCount())):
									row = layout.takeRow(i)
									field = row.fieldItem.widget()
									label = row.labelItem.widget().text()
									descr = self.get_control_value(field)
									if descr:
										unique = False
										if descr.endswith("{unique}"):
											unique = True
											descr = descr[:-8].strip()
										self._groups[key].append([label, field.__class__, descr, unique])
						self.clear_control(ctrl)
			else:
				queries = parse_query(self.get_control_value(ctrl))
				if queries:
					self._queries[key] = queries
					ctrl._queries = queries
					ctrl._descr = queries[0][1]
				self.clear_control(ctrl)
				self.bind_control(ctrl)
		
		cls_done = []
		found = True
		while found:
			found = False
			for key in self._queries:
				if key in self._key_order:
					continue
				for cls1, _, _, cls2, _ in self._queries[key]:
					if (cls2 in cls_done) or (cls2 == "{primary}"):
						self._key_order.append(key)
						found = True
						if cls1 not in cls_done:
							cls_done.append(cls1)
						break

	def get_selected(self):
		
		current = self.parent.parent.view.mdiarea.get_current()
		if current and hasattr(current, "get_selected_objects"):
			objects = list(current.get_selected_objects().values())
			if len(objects) == 1:
				return objects[0].id
		return None
	
	def set_item_value(self, key, ids, default = ""):
		
		def get_new_values(group_ctrl):
			
			ret = [] # [{descr: value, ...}, ...]
			for frame in group_ctrl.findChildren(QtWidgets.QFrame):
				ret_frame = {}
				for ctrl in frame.findChildren(QtWidgets.QWidget):
					if hasattr(ctrl, "_new") and ctrl._new:
						value = self.get_control_value(ctrl)
						if value:
							ret_frame[ctrl._descr] = value
				if ret_frame:
					ret.append(ret_frame)
			return ret[::-1]

		def is_last_frame_empty(group_ctrl):

			frame_nr = -1
			ret_frame = None
			for frame in group_ctrl.findChildren(QtWidgets.QFrame):
				ret_frame = {}
				for ctrl in frame.findChildren(QtWidgets.QWidget):
					if hasattr(ctrl, "_new") and ctrl._new:
						value = self.get_control_value(ctrl)
						ret_frame[ctrl._descr] = value
						frame_nr = ctrl._frame_nr
			if ret_frame == None:
				return False, frame_nr
			return (len(ret_frame) > 0) and (False not in [(ret_frame[descr] == "") for descr in ret_frame]), frame_nr
		
		def set_control(ctrl, value, cls, descr, default = ""):
			
			if value is None:
				value = default
			else:
				value = str(value)
			ctrl.blockSignals(True)
			if isinstance(ctrl, QtWidgets.QComboBox):
				ctrl.clear()
				values = []
				if descr is not None:
					for id2 in self.store.classes[cls].objects:
						value2 = self.store.objects[id2].descriptors[descr].label.value
						if (value2 is not None) and (value2 != value):
							values.append(str(value2))
				if value or values:
					values = [value] + values
					ctrl.addItems(values)
			elif isinstance(ctrl, QtWidgets.QLineEdit):
				ctrl.setText(value)
			elif isinstance(ctrl, QtWidgets.QPlainTextEdit):
				ctrl.setPlainText(value)
			ctrl.blockSignals(False)

		def add_group_frame(group_ctrl):
			
			frame = QtWidgets.QFrame(group_ctrl)
			frame.setLayout(QtWidgets.QFormLayout())
			frame.setStyleSheet("font-weight: normal;")
			group_ctrl.layout().addWidget(frame)
			return frame
		
		def add_group_frame_row(frame, label, field_class, frame_nr, queries, descr2, unique):
			
			label = QtWidgets.QLabel(label)
			field = field_class()
			if isinstance(field, QtWidgets.QComboBox):
				field.setEditable(True)
			label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			self.bind_control(field)
			field._queries = queries
			field._descr = descr2
			field._unique = unique
			field._frame_nr = frame_nr
			frame.layout().insertRow(0, label, field)
			frame.adjustSize()
			return field

		ctrl = self.__dict__[key]
		if key in self._groups:
			is_empty, frame_nr = is_last_frame_empty(ctrl)
			if not is_empty:
				frame = add_group_frame(ctrl)
				cls = self._queries[key][0][0]
				for label, field_class, descr2, unique in self._groups[key]:
					field = add_group_frame_row(frame, label, field_class, frame_nr, self._queries[key], descr2, unique)
					field._new = True
					set_control(field, "", cls, descr2)

		if key in self._edited:
			return
		cls, descr1, _, _, _ = self._queries[key][0]
		if key in self._groups:
			new_values = get_new_values(ctrl) # {descr: value, ...}
			self.clear_control(ctrl)
			frame_nr = 0
			ids_add = ids.copy()
			if new_values:
				ids_add += [-2] * len(new_values) + [-1]
				if key not in self._edited:
					self._edited.append(key)
			else:
				ids_add += [-1]
			for id in ids_add:
				if id < 0:
					obj = None
				else:
					obj = self.store.objects[id]
				new_values_id = {}
				if id == -2:
					new_values_id = new_values.pop()
				frame = add_group_frame(ctrl)
				for label, field_class, descr2, unique in self._groups[key]:
					field = add_group_frame_row(frame, label, field_class, frame_nr, self._queries[key], descr2, unique)
					field._new = (id < 0)
					value = None
					if obj is not None:
						value = obj.descriptors[descr2].label.value
					elif (id == -2) and (descr2 in new_values_id):
						value = new_values_id[descr2]
					set_control(field, value, cls, descr2)
				frame_nr += 1
		else:
			value = None
			if ids:
				value = self.store.objects[ids[0]].descriptors[descr1].label.value
			set_control(ctrl, value, cls, descr1, default)

	def get_obj_by_descr(self, cls, descr, value):
		
		if (descr is None) or (value is None):
			return None
		for id in self.store.classes[cls].objects:
			value2 = self.store.objects[id].descriptors[descr].label.value
			if value2 is not None:
				if str(value2) == str(value):
					return id
		return None
	
	def update_controls(self):
		
		key_order = self._key_order
		if self._edit_sender is not None:
			for key0 in self._key_order:
				if self.__dict__[key0] == self._edit_sender:
					key_order = [key0] + [key for key in self._key_order if key != key0]
					if key0 not in self._edited:
						self._edited.append(key0)
					break
		
		selected = self.get_selected()
		self._obj_lookup.clear()
		done = []
		found = True
		while found:
			found = False
			for key in key_order:
				if key in done:
					continue
				id_current = None
				value_current = self.get_control_value(key)
				if value_current:
					cls1, descr, _, _, unique = self._queries[key][0]
					id_current = self.get_obj_by_descr(cls1, descr, value_current)
					if unique and (key in self._edited) and (id_current is not None):
						self._edited.remove(key)
						for key1 in self._key_order:
							cls2, _, _, _, unique1 = self._queries[key1][0]
							if (not unique1) and (cls2 == cls1) and (key1 in self._edited):
								self._edited.remove(key1)
								self.clear_control(key1)
				
				for qry_idx in range(len(self._queries[key])):
					
					cls1, descr, rel, cls2, unique = self._queries[key][qry_idx]
					
					if cls1 in self._obj_lookup:
						done.append(key)
						self.set_item_value(key, self._obj_lookup[cls1])
						found = True
						break
					
					if cls2 in self._obj_lookup:
						id2 = self._obj_lookup[cls2][0]
						ids1 = []
						for id in self.store.objects[id2].relations[rel]:
							if cls1 in self.store.objects[id].classes:
								ids1.append(id)
						if ids1:
							if key not in self._edited:
								self._obj_lookup[cls1] = ids1
							done.append(key)
							self.set_item_value(key, ids1)
							found = True
							break

					if (qry_idx == len(self._queries[key]) - 1) and (id_current is not None):
						if key not in self._edited:
							self._obj_lookup[cls1] = [id_current]
						done.append(key)
						found = True
						break
					
					if (cls2 == "{primary}") and (selected is not None) and (selected in self.store.classes[cls1].objects):
						if key not in self._edited:
							self._obj_lookup[cls1] = [selected]
						done.append(key)
						self.set_item_value(key, [selected])
						break
		for key in self._groups:
			if key not in done:
				self.set_item_value(key, [])
		self.adjustSize()
	
	def reset_controls(self):
		
		for key in self._key_order:
			self.clear_control(key)
			self.set_item_value(key, [])
		self._edit_sender = None
		self._edited = []
		self._obj_lookup.clear()
		self.submitButton.setEnabled(False)
	
	def validate(self):
		
		ctrls = []
		for ctrl in self.findChildren(QtWidgets.QWidget):
			if hasattr(ctrl, "_queries"):
				ctrls.append(ctrl)
		
		filled_cls = []
		for ctrl in ctrls:
			cls, _, _, _, unique = ctrl._queries[0]
			if unique:
				value = self.get_control_value(ctrl)
				if value and (cls not in filled_cls):
					filled_cls.append(cls)
		
		required_cls = filled_cls.copy()
		missing_cls = []
		found = True
		while found:
			found = False
			for key in self._queries:
				cls1 = self._queries[key][0][0]
				if cls1 in required_cls:
					valid = False
					cls2s = []
					for _, _, _, cls2, _ in self._queries[key]:
						cls2s.append(cls2)
						if cls2 in filled_cls:
							valid = True
							break
					if not valid:
						for cls2 in cls2s:
							if cls2 not in missing_cls:
								missing_cls.append(cls2)
								found = True
							if cls2 not in required_cls:
								required_cls.append(cls2)
		
		valid = True
		for ctrl in ctrls:
			cls, _, _, _, unique = ctrl._queries[0]
			if unique and (cls in missing_cls):
				valid = False
				ctrl.setStyleSheet("font-weight: normal; background-color: #ffd199;")
			else:
				ctrl.setStyleSheet("font-weight: normal;")
		
		self.submitButton.setEnabled(valid and (len(self._edited) > 0))
	
	def submit(self):
		
		self._obj_lookup.clear()
		obj_lookup_groups = defaultdict(lambda: defaultdict(list)) # {cls: {frame_nr: [id], ...}, ...}
		inserted = [] # [[obj_id, queries, frame_nr], ...]
		for ctrl in self.findChildren(QtWidgets.QWidget):
			if hasattr(ctrl, "_queries"):
				frame_nr = -1
				if hasattr(ctrl, "_frame_nr"):
					frame_nr = ctrl._frame_nr
				cls = ctrl._queries[0][0]
				descr = ctrl._descr
				if frame_nr > -1:
					obj_lookup = obj_lookup_groups[cls][frame_nr]
				else:
					obj_lookup = self._obj_lookup[cls]
				value = self.get_control_value(ctrl)
				if value:
					if len(obj_lookup):
						id = obj_lookup[0]
					else:
						id = self.get_obj_by_descr(cls, descr, value)
					if id is None:
						obj = self.store.classes.add(cls).objects.add()
						id = obj.id
					else:
						obj = self.store.objects[id]
					obj.descriptors.add(descr, value)
					if id not in obj_lookup:
						if frame_nr > -1:
							obj_lookup_groups[cls][frame_nr].append(id)
						else:
							self._obj_lookup[cls].append(id)
					inserted.append([id, ctrl._queries, frame_nr])
		for id1, queries, frame_nr in inserted:
			for _, _, rel, cls2, _ in queries:
				if rel is None:
					continue
				for id2 in self._obj_lookup[cls2]:
					self.store.objects[id1].relations.add(self.store.reverse_relation(rel), id2)
		
	def on_activate(self):
		
		self.reset_controls()
		self.update_controls()
		self.validate()
		self.activateWindow()
		self.raise_()
	
	def on_edit(self):
		
		self._edit_timer.start(1000)
		self._edit_sender = self.sender()
	
	def on_edit_timer(self):
		
		self.update_controls()
		self.validate()
	
	@QtCore.pyqtSlot()
	def on_resetButton_clicked(self):
		
		self.reset_controls()
	
	@QtCore.pyqtSlot()
	def on_submitButton_clicked(self):
		
		self.submit()
		self.reset_controls()