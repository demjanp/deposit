from deposit.commander.usertools.DialogForm import (DialogForm)

from PySide2 import (QtWidgets, QtCore, QtGui)
from collections import defaultdict

class DialogEntryForm(DialogForm):
	
	def __init__(self, model, view, form_tool, selected_id):
		
		self.selected_id = selected_id
		self.selects = []
		
		DialogForm.__init__(self, model, view, form_tool)
		
		if self.view.usertools.entry_form_geometry is not None:
			self.setGeometry(self.view.usertools.entry_form_geometry)
		else:
			self.setMinimumWidth(600)
		
		self.overrideWindowFlags(QtCore.Qt.Window)
		
		if self.selected_id is not None:
			self.populate()
	
	def find_relations(self):
		# find all possible relations
		# returns frames, framesets, relations
		# frames = [DialogFrame(), ...]
		# framesets = [[DialogFrame(), ...], ...]
		# relations = [[cls1, rel, cls2], ...]
		
		relations = []  # [[cls1, rel, cls2], ...]
		classes = set()
		frames, framesets = self.frames()
		for frame in frames:
			classes.add(frame.dclass)
		for frameset in framesets:
			for frame in frameset:
				classes.add(frame.dclass)
		for cls1 in classes:
			for rel in self.model.classes[cls1].relations:
				if rel[0] == "~":
					continue
				for cls2 in self.model.classes[cls1].relations[rel]:
					if cls2 in classes:
						relations.append([cls1, rel, cls2])
		return frames, framesets, relations
	
	def populate(self):
		
		# find all possible relations
		frames, framesets, relations = self.find_relations()  # [[cls1, rel, cls2], ...]
		collect = []
		for cls1, rel, cls2 in relations:
			rel_rev = self.model.reverse_relation(rel)
			collect.append([cls2, rel_rev, cls1])
		relations += collect
		
		# find classes from multi groups
		multi_classes = defaultdict(set)  # {cls: set(group, ...), ...}
		for group in self.multigroups():
			for frameset in group.framesets():
				for frame in frameset:
					multi_classes[frame.dclass].add(group)
		
		# get all relevant objects
		objects = defaultdict(list)  # {class: [object, ...], ...}
		obj = self.model.objects[self.selected_id]
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
		
		# fill single entry frames
		for frame in frames:
			if frame.dclass not in data:
				continue
			obj_id = next(iter(data[frame.dclass]))
			if frame.descriptor in data[frame.dclass][obj_id]:
				frame.set_value(data[frame.dclass][obj_id][frame.descriptor])
		
		# fill multi entry fields
		group_ids = defaultdict(set)  # {obj_id: set(group, ...), ...}
		frameset_values = defaultdict(lambda: defaultdict(dict))  # {obj_id: {cls: {descriptor: value, ...}, ...}, ...}
		for cls in multi_classes:
			if cls not in data:
				continue
			for obj_id in data[cls]:
				group_ids[obj_id].update(multi_classes[cls])
				for descr in data[cls][obj_id]:
					value = data[cls][obj_id][descr]
					if value is not None:
						frameset_values[obj_id][cls][descr] = value
		for obj_id in frameset_values:
			for group in group_ids[obj_id]:
				frameset = group.framesets()[-1]
				for frame in frameset:
					if (frame.dclass in frameset_values[obj_id]) and (frame.descriptor in frameset_values[obj_id][frame.dclass]):
						frame.set_value(frameset_values[obj_id][frame.dclass][frame.descriptor])
				group.add_entry()
		self.adjust_labels()
		
	def submit(self):
		
		# find frames, framesets and all possible relations
		frames, framesets, relations = self.find_relations()
		# frames = [DialogFrame(), ...]
		# framesets = [[DialogFrame(), ...], ...]
		# relations = [[cls1, rel, cls2], ...]
		
		# collect values from form
		values = defaultdict(lambda: defaultdict(dict)) # {cls: {idx: {descr: value, ...}, ...}, ...}
		for frame in frames:
			value = frame.get_value()
			if value == "":
				value = None
			values[frame.dclass][0][frame.descriptor] = value
		idx = -1
		for frameset in framesets:
			idx += 1
			for frame in frameset:
				value = frame.get_value()
				if value == "":
					value = None
				values[frame.dclass][idx][frame.descriptor] = value
		
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
	
	def clear(self):
		
		for group in self.multigroups():
			group.clear()
		frames, _ = self.frames()
		for frame in frames:
			frame.set_value("")
	
	def on_submit(self, *args):
		
		self.submit()
		self.clear()
	
	def on_reset(self, *args):
		
		self.clear()

	
	def closeEvent(self, event):
		
		self.view.usertools.entry_form_geometry = self.geometry()
		DialogForm.closeEvent(self, event)

