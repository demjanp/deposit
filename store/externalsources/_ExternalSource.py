from deposit.DModule import (DModule)
from deposit.store.Query.Parse import (find_quotes, Select)

from collections import defaultdict

class ExternalSource(DModule):
	
	def __init__(self, store, url):

		self.store = store
		self.url = url

		DModule.__init__(self)
	
	@property
	def name(self):
		
		return self.__class__.__name__
	
	def import_data(self, sheet, targets):
		# targets = {column_idx: target, ...}
		
		def has_labels(obj, labels):
			# returns a list of descriptors to be set or True or False
			
			to_set = []
			for descr in labels:
				if descr not in obj.descriptors:
					to_set.append(descr)
				if obj.descriptors[descr].label.value != labels[descr].value:
					return False
			if to_set:
				return to_set
			return True
		
		# collect target classes & descriptors
		for idx in list(targets.keys()):
			selectstr, quotes = find_quotes(targets[idx])
			select = Select(self.store, selectstr, quotes)
			if (len(select.classes) != 1) or (len(select.descriptors) != 1) or (list(select.classes)[0][-1] == "*"):
				del targets[idx]
			else:
				targets[idx] = [list(select.classes)[0], list(select.descriptors)[0]]
		# targets = {column_idx: [class, descriptor], ...}
		
		# create classes & descriptors (if they don't exist)
		classes = set()
		for column_idx in targets:
			cls, descr = targets[column_idx]
			self.store.classes.add(cls)
			self.store.classes.add(descr)
			classes.add(cls)
		
		# find relations between classes
		relations = []  # [[cls1, rel, cls2], ...]
		for cls1 in classes:
			for rel in self.store.classes[cls1].relations:
				if rel[0] == "~":
					continue
				for cls2 in self.store.classes[cls1].relations[rel]:
					if cls2 in classes:
						relations.append([cls1, rel, cls2])
		
		# add data
		for row_idx in range(self.row_count(sheet)):
			
			# collect labels by class & descriptor
			labels = defaultdict(dict)  # {cls: {descr: label, ...}, ...}
			for column_idx in targets:
				label = self.data(sheet, row_idx, column_idx)
				if label is None:
					continue
				cls, descr = targets[column_idx]
				labels[cls][descr] = label
			
			# find or add an object for each class
			obj_row = {} # {cls: object_id, ...}
			for cls in labels:
				
				# check if object with labels already exists
				to_set = False
				for id in self.store.classes[cls].objects:
					obj = self.store.objects[id]
					to_set = has_labels(obj, labels[cls])
					if to_set:
						break
				
				if to_set: # object found
					obj_row[cls] = obj
					if not isinstance(to_set, list):
						to_set = []
				else: # create object
					obj_row[cls] = self.store.objects.add()
					obj_row[cls].classes.add(cls)
					to_set = list(labels[cls].keys())
				
				# set descriptors of object
				for descr in to_set:
					obj_row[cls].descriptors.add(descr, labels[cls][descr])
			
			# create relations
			for cls1, rel, cls2 in relations:
				obj_row[cls1].relations.add(rel, obj_row[cls2])
	
	def load(self):
		# re-implement
		
		pass
	
	def sheets(self):
		# re-implement
		
		pass
	
	def column_count(self, sheet):
		# re-implement
		
		pass
	
	def row_count(self, sheet):
		# re-implement
		
		pass
	
	def column_name(self, sheet, column_idx):
		# re-implement
		
		pass
	
	def data(self, sheet, row_idx, column_idx):
		# re-implement
		
		pass
	
	def export_data(self, query):
		# re-implement
		
		pass
	