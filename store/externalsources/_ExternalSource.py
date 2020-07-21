from deposit.DModule import (DModule)
from deposit.store.Query.Parse import (find_quotes, Select)

from collections import defaultdict
from itertools import product

class ExternalSource(DModule):
	
	def __init__(self, store, url):

		self.store = store
		self.url = url

		DModule.__init__(self)
	
	@property
	def name(self):
		
		return self.__class__.__name__
	
	def import_data(self, sheet, targets, relations = []):
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
			select = Select(self.store, selectstr, quotes, create_classes = True)
			if (len(select.classes) != 1) or (len(select.descriptors) != 1) or (list(select.classes)[0][-1] == "*"):
				del targets[idx]
			else:
				targets[idx] = [list(select.classes)[0], list(select.descriptors)[0]]
		# targets = {column_idx: [class, descriptor], ...}
		
		# create classes & descriptors (if they don't exist)
		classes = set()
		for column_idx in targets:
			cls, descr = targets[column_idx]
			classes.add(cls)
		
		# find relations between classes
		for cls1 in classes:
			for rel in self.store.classes[cls1].relations:
				if rel[0] == "~":
					continue
				for cls2 in self.store.classes[cls1].relations[rel]:
					if cls2 in classes:
						if [cls1, rel, cls2] not in relations:
							relations.append([cls1, rel, cls2])
		
		# add data
		for row_idx in range(self.row_count(sheet)):
			
			# collect labels by class & descriptor
			labels = defaultdict(lambda: defaultdict(list))  # {cls: {descr: [label, ...], ...}, ...}
			for column_idx in targets:
				label = self.data(sheet, row_idx, column_idx)
				if label is None:
					continue
				cls, descr = targets[column_idx]
				labels[cls][descr].append(label)
			
			# find or add an object for each class
			obj_row = defaultdict(list) # {cls: [object, ...] ...}
			for cls in labels:
				
				for labels_row in product(*[labels[cls][descr] for descr in labels[cls]]):
					labels_cls = dict([(descr, labels_row[i]) for i, descr in enumerate(labels[cls])])
				
					# check if object with labels already exists
					to_set = False
					for id in self.store.classes[cls].objects:
						obj = self.store.objects[id]
						to_set = has_labels(obj, labels_cls)
						if to_set:
							break
					
					if to_set: # object found
						obj_row[cls].append(obj)
						if not isinstance(to_set, list):
							to_set = []
					else: # create object
						obj_row[cls].append(self.store.objects.add())
						obj_row[cls][-1].classes.add(cls)
						to_set = list(labels_cls.keys())
					
					# set descriptors of object
					for descr in to_set:
						obj_row[cls][-1].descriptors.add(descr, labels_cls[descr])
			
			# create relations
			for cls1, rel, cls2 in relations:
				for obj1 in obj_row[cls1]:
					for obj2 in obj_row[cls2]:
						obj1.relations.add(rel, obj2)
	
	def load(self):
		# re-implement
		
		pass
	
	def sheets(self):
		# re-implement
		
		return []
	
	def column_count(self, sheet):
		# re-implement
		
		return 0
	
	def row_count(self, sheet):
		# re-implement
		
		return 0
	
	def column_name(self, sheet, column_idx):
		# re-implement
		
		pass
	
	def data(self, sheet, row_idx, column_idx):
		# re-implement
		
		pass
	
	def export_data(self, query):
		# re-implement
		
		pass
	