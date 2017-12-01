from deposit.DLabel import (DString, DResource, DGeometry, DNone)
from deposit import (Query)
from rdflib import (URIRef)
import os
from PyQt5 import (QtWidgets, QtCore)

class ModelActions(object):
	
	def __init__(self, model):
		
		self.__model = model
	
	def __getattr__(self, key):
		
		return getattr(self.__model, key)
	
	def add_descriptor(self, name, obj_id, label):
		
		self.store.relations.add_descriptor(self.store.classes.add(name), obj_id, label)
	
	def add_geotag(self, name, obj_id, uri, coords):
		
		if not isinstance(uri, URIRef):
			uri = URIRef(uri)
		rel_id = self.store.relations.add_descriptor(self.store.classes.add(name), obj_id, uri)
		self.store.geotags.add(rel_id, coords)
	
	def add_resource(self, name, obj_id, label, local, cls_id = None):
		
		if cls_id is None:
			cls_id = self.store.classes.add(name)
		if local:
			uri = self.store.resources.add_local(label)
		else:
			uri = self.store.resources.add_remote(label)
		self.store.relations.add_descriptor(cls_id, obj_id, DResource(uri))
	
	def rename_class(self, cls_id, name):
		
		self.store.classes.set_label(cls_id, name)
	
	def delete_relation(self, obj_id1, label, obj_id2, reversed):
		
		rel_id = self.store.queryfnc.get_related_by_label(obj_id1, label, obj_id2, reversed)
		if not rel_id is None:
			self.store.relations.remove(rel_id)
	
	def import_data(self, data, fields, targets, merges, overwrite = False):
		# data = [{column: DLabel, ...}, ...]; in order of rows
		# fields = [name, ...]
		# targets = [traverse, traverse#Class.Descriptor, ...]; traverse: C.D / C.R.C.D
		#	specify multiple targets by separating traverses by ;
		#	in case traverse#Class.Descriptor is used, handle value as a quantifier of traverse summed over the specified Descriptor. Traverse must end in a Descriptor which is filled with the original column name
		#	e.g.: C1.R1.C2.D1 # CX.D2 -> C1.R1.C2.D1 = column name; CX.D2 = value; CX can be C1 or C2
		# merges = [True/False, ...]; in order of targets; specifies whether imported row should be merged with existing Objects based on this Descriptor
		
		def _import_columns(data, row, columns, classes, descriptors, quantifiers, targets, to_merge):
			
			collect = [column for column in columns if (column in to_merge)]
			collect += [column for column in columns if (not column in collect)]
			columns = collect
			
			cls_obj = {} # {class_name: obj_id, ...}
			for column in columns:
				if not column in targets:
					continue
				
				# get value
				value = data[row][column]
				if isinstance(value, DNone):
					continue
				
				# get quantifier
				quan_value = None
				if column in quantifiers:
					quan_value = value
					value = DString(fields[column])
				
				try_merge = (column in to_merge)
				for target in targets[column]:
					
					found_objects = []
					if try_merge:
						cls, descr = target[-2], target[-1]
						if isinstance(cls, list):
							cls = cls[-1]
						qry = Query(self.store, "%(cls)s.%(descr)s == \"%(value)s\"" % dict(cls = cls, descr = descr, value = value.value))
						found_objects = qry.keys()
						if cls in cls_obj:
							found_objects = [obj for obj in found_objects if not obj in cls_obj[cls]]
						if found_objects:
							cls_obj[cls] = found_objects.copy()
						else:
							try_merge = False
							'''
							if cls in cls_obj:
								del cls_obj[cls]
							''' # TODO test if this does not break importing
					
					# create objects & relations & add descriptors
					if len(target) == 2: # C.D
						cls, descr = target
						if not cls in cls_obj:
							cls_obj[cls] = [self.store.objects.add()]
							self.store.members.add(classes[cls], cls_obj[cls][0])
						self.store.relations.add_descriptor(descriptors[descr], cls_obj[cls][0], value)
					
					else: # C.R.C...D
						cls1 = target[0]
						if not cls1 in cls_obj:
							cls_obj[cls1] = [self.store.objects.add()]
							self.store.members.add(classes[cls1], cls_obj[cls1][0])
						prev_obj = cls_obj[cls1][0]
						for rel, cls2 in target[1:-1]:
							if not cls2 in cls_obj:
								cls_obj[cls2] = [self.store.objects.add()]
								self.store.members.add(classes[cls2], cls_obj[cls2][0])
							if rel.startswith("~"):
								self.store.relations.add(cls_obj[cls2][0], prev_obj, rel.strip("~"))
							else:
								self.store.relations.add(prev_obj, cls_obj[cls2][0], rel)
							prev_obj = cls_obj[cls2][0]
						self.store.relations.add_descriptor(descriptors[target[-1]], prev_obj, value)
				
				# add quantifier descriptor
				if not quan_value is None:
					cls, descr = quantifiers[column]
					if not cls in cls_obj:
						cls_obj[cls] = [self.store.objects.add()]
						self.store.members.add(classes[cls], cls_obj[cls][0])
					self.store.relations.add_descriptor(descriptors[descr], cls_obj[cls][0], quan_value)
		
		columns = len(fields)
		rows = len(data)
		
		self.store.begin_change()
		
		# analyse target traverses & create classes
		classes = {} # {class_name: cls_id, ...}
		descriptors = {} # {descr_name: cls_id, ...}
		quantifiers = {} # {column: [class, descriptor], ...}
		collect = {} # {column: [[class_name, descr_name], [class_name, [[rel_label, class_name], ...], descr_name], ...], ...}
		for column, target in enumerate(targets):
			if "#" in target:
				target, quantifier = target.split("#")
				quantifiers[column] = quantifier.strip().split(".") # [C,D]
				if not quantifiers[column][0] in classes:
					classes[quantifiers[column][0]] = self.store.classes.add(quantifiers[column][0])
				if not quantifiers[column][1] in descriptors:
					descriptors[quantifiers[column][1]] = self.store.classes.add(quantifiers[column][1])
			target = target.strip().split(";")
			collect[column] = []
			for traverse in target:
				traverse = traverse.split(".")
				for j in range(0, len(traverse), 2):
					if not traverse[j] in classes:
						classes[traverse[j]] = self.store.classes.add(traverse[j])
				if not traverse[-1] in descriptors:
					descriptors[traverse[-1]] = self.store.classes.add(traverse[-1])
				if len(traverse) == 2: # C.D
					collect[column].append([traverse[0], traverse[1]])
				else: # C.R.C...D
					collect[column].append([traverse[0]] + [[traverse[j - 1], traverse[j]] for j in range(2, len(traverse), 2)] + [traverse[-1]])
		targets = collect
		to_merge = [column for column in range(columns) if merges[column]] # [column, ...]
		tgt_in_columns = {} # {str(target): [column, ...], ...}
		for target in targets.values():
			key1 = str(target)
			if not key1 in tgt_in_columns:
				tgt_in_columns[key1] = []
				for column in targets:
					key2 = str(targets[column])
					if key2 == key1:
						tgt_in_columns[key1].append(column)
		single_columns = [value[0] for value in tgt_in_columns.values() if (len(value) == 1)]
		multi_columns = [value for value in tgt_in_columns.values() if (len(value) > 1)]
		
		# classes = {class_name: cls_id, ...}
		# descriptors = {descr_name: cls_id, ...}
		# quantifiers = {column: [class, descriptor], ...}
		# targets = {column: [[class_name, descr_name], [class_name, [[rel_label, class_name], ...], descr_name], ...], ...}
		# to_merge = [column, ...]
		# single_columns = [column, ...]
		# multi_columns = [[column, ...], ...]
		
		for row in range(rows):

			self.store.message("Importing row: %d/%d" % (row + 1, rows))
			print("\rImporting row: %d/%d" % (row + 1, rows), end = "")
			
			if multi_columns:
				# if multiple columns have the same target specified, execute import for each combination of them + all single columns
				if len(multi_columns) == 1:
					for columns in multi_columns:
						for column in columns:
							_import_columns(data, row, single_columns + [column], classes, descriptors, quantifiers, targets, to_merge)
				else:
					for columns1 in multi_columns:
						for columns2 in multi_columns:
							if columns1 != columns2:
								for column1 in columns1:
									for column2 in columns2:
										if column1 != column2:
											_import_columns(data, row, single_columns + [column1, column2], classes, descriptors, quantifiers, targets, to_merge)
			else:
				_import_columns(data, row, single_columns, classes, descriptors, quantifiers, targets, to_merge)
		
		self.store.end_change()
	
	def check_in(self, ident):
		
		state, missing_members, missing_relations, duplicate_descriptors = self.store.check_in(ident, overwrite = self.check_in_collisions_overwrite())
		if state != True:
			QtWidgets.QMessageBox.information(self._view, "Check In Failed", state)
		else:
			# TODO display results via GUI
			# missing_members = [[id_src, id_tgt], ...]; Members not checked in due to deletion in source database
			# missing_relations = [[id_src, id_tgt, label], ...]; Relations not checked in due to deletion in source database
			# duplicate_descriptors = {name: cls_id, ...}; Descriptors created due to colisions (Descriptor -> label -> Object combination exists in source database with a different label)
			print()
			print("Members not checked in due to deletion in source database:")
			print(missing_members)
			print()
			print("Relations not checked in due to deletion in source database:")
			print(missing_relations)
			print()
			print("Descriptors created due to colisions:")
			print(duplicate_descriptors)
			print()
