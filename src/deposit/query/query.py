'''
Query
	.querystr
	.columns = [(class_name, descriptor_name), (None, alias), ...]
	.classes = [class_name, ...]
	.objects = {obj_id, ...}
	.main_class = class_name
	.hash
	.parse
		.classes = {name, ...}
		.descriptors = {name, ...}
		.querystr
		.columns = [(class_name, descriptor_name), (None, alias), ...]
		.selects = [(class_name, descriptor_name), ...]
		.group_by = [(class_name, descriptor_name), ...]
		.counts = [(alias, class_name, descriptor_name), ...]
		.sums = [(alias, class_name, descriptor_name), ...]
		.relations = [(class1, relation, class2), ...]
		.where_expr = python expression
		.where_vars = {name: (class, descriptor), ...}
			use: eval(where_expr, {name: value of descriptor of object which is member of class, ...})
		.classes_used = [name, ...]

Query[row, column] / [row, Class_name, Descriptor_name] / [row, "Class_name.Descriptor_name"] = (obj_id, value)

value = python type / DDateTime / DGeometry / DResource

DDateTime
	.value = datetime.datetime
	.isoformat = value in ISO format

DGeometry
	.value = (geometry_type, coords, srid, srid_vertical)
	.geometry_type = POINT etc.
	.coords = []
	.srid
	.srid_vertical
	.wkt = WKT string

DResource
	.value = (url, filename, is_stored, is_image)
	.url
	.filename
	.is_stored
	.is_image
	.object_ids = set()
	
	
'''

from deposit.query.parse import Parse
from deposit.store.abstract_dtype import AbstractDType

from collections import defaultdict
from natsort import (natsorted)
from itertools import product
import traceback
import sys

class Query(object):
	
	def __init__(self, store, querystr, progress = None):
		
		self.querystr = querystr
		self.parse = None
		self.hash = [] # hash of the query rows (to quickly check whether query has changed)
		
		self._store = store
		self._rows = []
		self._columns = []
		self._classes = []
		self._objects = set()
		self._main_class = None
		self._progress = progress
		
		self.process()
	
	def set_progress(self, progress):
		
		self._progress = progress
	
	def _get_descriptor_value(self, obj_id, class_name, descriptor_name, class_lookup, descr_lookup, obj_if_none = False):
		
		if class_name not in class_lookup[obj_id][0]:
			return None
		
		if descriptor_name is None:
			if obj_if_none:
				return obj_id
			return None
		
		return descr_lookup[obj_id].get((class_name, descriptor_name), None)
	
	def _get_order(self, class_name, descriptor_name):
		
		order = []
		for name in [class_name, descriptor_name]:
			if self._store.has_class(name):
				order.append(self._store.get_class(name).order)
			else:
				order.append(None)
		return order
	
	def process(self):
		
		self._process()  # DEBUG
		return  # DEBUG
		
		try:
			self._process()
		except:
			_, exc_value, _ = sys.exc_info()
			self._store.callback_error(
				"QUERY ERROR in \"%s\": %s" % (self.querystr, str(exc_value))
			)
	
	def _obj_func(self, *args):
		# Function to handle OBJ(*args) in the query
		# Accepts one or more object ids
		# Returns a list of objects or None
		
		obj_ids = [self._store.get_object(obj_id) for obj_id in args]
		obj_ids = [obj_id for obj_id in obj_ids if obj_id is not None]
		return obj_ids
	
	def _has_relation(self, elements1, elements2, label, chained=False):
		# Function to handle RELATED(elements1, elements2, label, chained) in the query
		# elements can be a list of Objects or a single Object ID
		# If chained==True, look for chained relations
		
		def _element_to_object(element):
			
			if isinstance(element, int):
				return self._store.get_object(element)
			return element
		
		def _elements_to_objects(elements):
			if isinstance(elements, set) or isinstance(elements, list):
				objs = [_element_to_object(element) for element in elements]
				objs = set([obj for obj in objs if obj is not None])
			else:
				objs = set()
				obj = _element_to_object(elements)
				if obj is not None:
					objs = set([obj])
			return objs
		
		objects1 = _elements_to_objects(elements1)
		objects2 = _elements_to_objects(elements2)
		if (not objects1) or (not objects2):
			return False
		objects_all = objects1.union(objects2)
		objects_found = set()
		for obj1 in objects1:
			for obj2 in objects2:
				if obj1.has_relation(obj2, label, chained):
					objects_found.add(obj1)
					objects_found.add(obj2)
					break
		if objects_all.issubset(objects_found):
			return True
		return False
	
	def _process(self):
		
		self.hash = []
		self._rows = []
		self._columns = []
		self._column_idxs = {}
		self._classes = []
		self._objects = set()
		self._main_class = None
		
		self.parse = Parse(
			self.querystr,
			set([cls.name for cls in self._store.get_classes()]),
			set(self._store.get_descriptor_names())
		)
		selects = []
		for class_name, descriptor_name in self.parse.selects:
			if (class_name not in self.parse.classes) and (class_name not in ["*", "!*"]) and (not isinstance(class_name, tuple)):
				continue
			if (descriptor_name not in self.parse.descriptors) and (descriptor_name not in [None, "*"]):
				continue
			selects.append((class_name, descriptor_name))
		if not selects:
			self._store.callback_error(
				"QUERY ERROR in \"%s\": no SELECT statement found" % (self.querystr)
			)
			return
		
		self._main_class = selects[0][0]
		
		keys_all = set()  # {(class_name, descriptor_name), ...}
		for class_name, descriptor_name in selects:
			keys_all.add((class_name, descriptor_name))
			if class_name not in self._classes:
				self._classes.append(class_name)
			if descriptor_name not in self._classes:
				self._classes.append(descriptor_name)
		alias_lookup = {}
		for alias, class_name, descriptor_name in self.parse.counts:
			keys_all.add((class_name, descriptor_name))
			alias_lookup[alias] = ("count", class_name, descriptor_name)
			if class_name not in self._classes:
				self._classes.append(class_name)
		for alias, class_name, descriptor_name in self.parse.sums:
			keys_all.add((class_name, descriptor_name))
			alias_lookup[alias] = ("sum", class_name, descriptor_name)
			if class_name not in self._classes:
				self._classes.append(class_name)
		value_lookup = {}
		for name in self.parse.where_vars:
			value_lookup[self.parse.where_vars[name]] = name
		key_lookup = defaultdict(set)
		
		# get connected objects based on selects and relations
		paths = self._store.get_linked_objects(
			self.parse.classes_used, 
			self.parse.relations, 
			progress = self._progress
		)
		
		obj_ids = set()
		for path in paths:
			obj_ids.update(path)
		
		cmax = len(paths) + len(obj_ids)
		cnt = 1
		
		class_lookup = {}  # {obj_id: [classes, superclasses], ...}
		class_descr_lookup = {"!*": [], "*": []}
		for obj_id in obj_ids:
			class_lookup[obj_id] = [set(), set()]
		for class_name in self._classes:
			class_descr_lookup[class_name] = []
			cls = self._store.get_class(class_name)
			if cls is not None:
				class_descr_lookup[class_name] = cls.get_descriptor_names()
				for tgt in self._store.G.iter_class_children(cls.name):
					if tgt in class_lookup:
						class_lookup[tgt][0].add(cls.name)
				for tgt in self._store.G.iter_class_descendants(cls.name):
					if tgt in class_lookup:
						class_lookup[tgt][1].add(cls.name)
		for obj_id in obj_ids:
			if not class_lookup[obj_id][0]:
				class_lookup[obj_id][0].add(None)
		
		descr_lookup = {}  # {obj_id: {(class_name, descriptor_name): value, ...}, ...}
		class_names = set()
		for obj_id in obj_ids:
			if (self._progress is not None) and (cnt % 20000 == 0):
				self._progress.update_state(text = "Populating Query", value = cnt, maximum = cmax)
			cnt += 1
			descr_lookup[obj_id] = {}
			obj = self._store.G.get_object_data(obj_id)
			for descr in obj._descriptors:
				classes = class_lookup[obj_id][0].union(class_lookup[obj_id][1])
				if classes:
					for class_name in classes:
						descr_lookup[obj_id][(class_name, descr.name)] = obj._descriptors[descr]
				else:
					descr_lookup[obj_id][(None, descr.name)] = obj._descriptors[descr]
		
		rows = []  # [(obj, {key: value, ...}), ...]; key = (class_name, descriptor_name)
		done = set()  # {(obj_id, ...), ...}; to avoid duplicate rows
		keys_collect = set()  # {(class_name, descriptor_name), ...}
		for path in paths:
			if (self._progress is not None) and (cnt % 20000 == 0):
				self._progress.update_state(text = "Populating Query", value = cnt, maximum = cmax)
			cnt += 1
			# filter paths by evaluating WHERE expression for each
			values = {}  # {name: value, ...}
			if self.parse.where_expr:
				# collect descriptor values for each path object according to WHERE (Parse.where_vars)
				for name in self.parse.where_vars:
					values[name] = None
				for obj_id in path:
					class_names = class_lookup[obj_id][0]
					for name in self.parse.where_vars:
						class_name, descriptor_name = self.parse.where_vars[name]
						if class_name == "!*":
							class_name = None
						if (not isinstance(class_name, tuple)) and class_names and (class_name not in class_names):
							continue
						value = self._get_descriptor_value(obj_id, class_name, descriptor_name, class_lookup, descr_lookup, obj_if_none = True)
						if value is not None:
							if values[name] is not None:
								if not isinstance(values[name], set):
									values[name] = set([values[name]])
								values[name].add(value)
							else:
								values[name] = value
				values["OBJ"] = self._obj_func
				values["RELATED"] = self._has_relation
				
				
				res = False
				try:
					res = eval(self.parse.where_expr, values)
				except:
					_, exc_value, _ = sys.exc_info()
					self._store.callback_error(
						"QUERY ERROR in WHERE statement \"%s\": %s" % (self.querystr, str(exc_value))
					)
					return
				
				if not res:
					continue
			
			# collect descriptor values according to SELECT, COUNT, SUM
			data = defaultdict(list)  # {key: set(value, ...), ...}; key = (class_name, descriptor_name)
			for obj_id in path:
				self._objects.add(obj_id)
				class_names = class_lookup[obj_id][1]
				for key in keys_all:
					class_name, descriptor_name = key
					if (not isinstance(class_name, tuple)) and (class_name[-1] != "*") and (class_name not in class_names):
						continue
					if isinstance(class_name, tuple) and (obj_id not in list(class_name)):
						continue
					if class_name == "*":
						class_name = class_names[0] if class_names else None
					elif class_name == "!*":
						class_name = None
					if descriptor_name != "*":
						data[(class_name, descriptor_name)].append((obj_id, self._get_descriptor_value(obj_id, class_name, descriptor_name, class_lookup, descr_lookup)))
						key_lookup[key].add((class_name, descriptor_name))
					else:
						descriptor_names = class_descr_lookup["!*" if class_name is None else class_name]
						for _, descriptor_name in descr_lookup[obj_id]:
							if descriptor_name not in descriptor_names:
								descriptor_names.append(descriptor_name)
						if descriptor_names:
							for descriptor_name in descriptor_names:
								data[(class_name, descriptor_name)].append((obj_id, self._get_descriptor_value(obj_id, class_name, descriptor_name, class_lookup, descr_lookup)))
								key_lookup[key].add((class_name, descriptor_name))
						else:
							data[(class_name, None)].append((obj_id, None))
							key_lookup[key].add((class_name, None))
			keys_data = list(data.keys())
			keys_collect.update(keys_data)
			for vals in product(*(data[key] for key in keys_data)):
				data_row = dict(zip(keys_data, vals)) # {key: value, ...}; key = (class_name, descriptor_name)
				check_row = tuple(sorted([val[0] for val in data_row.values()]))
				if check_row in done:
					continue
				done.add(check_row)
				rows.append((path[0], data_row))			
		
		# prune (class_name, None) from key_lookup if it already has (class_name, descriptor_name)
		for key in key_lookup:
			for class_name, descriptor_name in list(key_lookup[key]):
				if descriptor_name is None:
					for class_name2, descriptor_name2 in key_lookup[key]:
						if descriptor_name2 is None:
							continue
						if class_name2 == class_name:
							key_lookup[key].remove((class_name, None))
							break
		
		# generate keys for each column sorted according to Parse.columns
		keys_columns = []  # [(typ, alias, class_name, descriptor_name), ...]; typ = count / sum / None
		for class_name, descriptor_name in self.parse.columns:
			if class_name is None:
				if descriptor_name in alias_lookup:
					alias = descriptor_name
					typ_, class_name_, descriptor_name_ = alias_lookup[alias]
					if (class_name_, descriptor_name_) in keys_collect:
						keys_columns.append((typ_, alias, class_name_, descriptor_name_))
			elif (class_name, descriptor_name) in key_lookup:
				for class_name_, descriptor_name_ in natsorted(list(key_lookup[(class_name, descriptor_name)]), key = lambda row: self._get_order(*row)):
					if (class_name_, descriptor_name_) in keys_collect:
						keys_columns.append((None, None, class_name_, descriptor_name_))
		idxs_counts = []
		idxs_sums = []
		for idx, key in enumerate(keys_columns):
			typ, _, _, _ = key
			if typ == "count":
				idxs_counts.append(idx)
			elif typ == "sum":
				idxs_sums.append(idx)
		
		# group rows according to GROUP BY
		keys_group = [key for key in self.parse.group_by if key in keys_collect]
		grouped = defaultdict(list)
		for obj, data in rows:
			row = []
			group_key = []
			for key in keys_columns:
				typ, alias, class_name, descriptor_name = key
				row.append(data.get((class_name, descriptor_name), (None, None)))
				if (class_name, descriptor_name) in keys_group:
					group_key.append(str(row[-1]))
			row = tuple([obj] + row)
			if group_key:
				group_key = tuple(group_key)
			else:
				group_key = tuple([str(val) for val in row])
			grouped[group_key].append(row)
		
		# add query rows and count / sum grouped
		rows = []
		for group_key in grouped:
			if len(grouped[group_key]) == 1:
				row_collect = list(grouped[group_key].pop())
				obj = row_collect.pop(0)
				for idx in idxs_counts:
					row_collect[idx] = (None, int(row_collect[idx][0] is not None))
				for idx in idxs_sums:
					val = 0
					try:
						val = float(row_collect[idx][1])
					except:
						pass
					row_collect[idx] = (None, val)
			else:
				row_collect = [None] * len(keys_columns)
				for row in grouped[group_key]:
					row = list(row)
					obj = row.pop(0)
					for idx, key in enumerate(keys_columns):
						if idx in idxs_counts:
							if row_collect[idx] is None:
								row_collect[idx] = [None, 0]
							if row[idx] is not None:
								row_collect[idx][1] += 1
						elif idx in idxs_sums:
							if row_collect[idx] is None:
								row_collect[idx] = [None, 0]
							val = None
							try:
								val = float(row[idx][1])
							except:
								pass
							if val is not None:
								row_collect[idx][1] += val
						elif row_collect[idx] is None:
							row_collect[idx] = row[idx]
			rows.append([tuple(item) for item in row_collect])
		
		# sort and prune rows
		rows = natsorted(rows)[::-1]
		collect = []
		check_row_last = None
		for row in rows:
			check_row = set([item[0] if (item[0] is not None) else item[1] for item in row if item != (None, None)])
			if check_row_last is None:
				check_row_last = check_row
			elif check_row.issubset(check_row_last):
				continue
			check_row_last = check_row
			collect.append(row)
		rows = collect[::-1]
		
		# merge redundant rows
		if (len(rows) > 1) and (len(rows[0]) > 1):
			found = True
			while found:
				found = False
				collect = [rows[0]]
				last = rows[0]
				for row in rows[1:]:
					if row[0] != last[0]:
						collect.append(row)
						last = row
						continue
					isnone_row = set()
					isnone_last = set()
					merge = True
					for j in range(1, len(row)):
						if row[j] == (None, None):
							isnone_row.add(j)
						elif last[j] == (None, None):
							isnone_last.add(j)
						elif row[j] != last[j]:
							merge = False
							break
					if merge:
						found = True
						merged = collect[-1]
						for j in isnone_last:
							merged[j] = row[j]
						collect[-1] = merged
						last = merged
					else:
						collect.append(row)
						last = row
				rows = collect
		
		self._rows = rows
		
		if keys_columns:
			for _, alias, class_name, descriptor_name in keys_columns:
				if alias is None:
					self._columns.append((class_name, descriptor_name))
				else:
					self._columns.append((None, alias))
		else:
			for class_name, descriptor_name in self.parse.columns:
				self._columns.append((class_name, descriptor_name))
		
		for idx, key in enumerate(self._columns):
			self._column_idxs[key] = idx
		
#		self._rows = [[value, ...]]
#		self._columns = [(class_name, descriptor_name) or (None, alias)]
#		self._classes = [class_name, ...]
	
	@property
	def columns(self):
		# [(class_name, descriptor_name), (None, alias), ...]
		
		return self._columns.copy()
	
	@property
	def classes(self):
		# [class_name, ...]
		
		return self._classes.copy()
	
	@property
	def objects(self):
		# [obj_id, ...]
		
		return self._objects
	
	@property
	def main_class(self):
		
		return self._main_class
	
	def __len__(self):

		return len(self._rows)
	
	def __bool__(self):

		return len(self._rows) > 0
	
	def __getitem__(self, idx):
		# idx = (row, column) / (row, Class_name, Descriptor_name) / (row, "Class.Descriptor")
		#
		# returns (obj_id, value)
		
		if not isinstance(idx, tuple):
			raise IndexError()
		if not isinstance(idx[0], int):
			raise IndexError()
		row = idx[0]
		col = None
		if (len(idx) == 2) and isinstance(idx[1], int):
			col = idx[1]
		elif (len(idx) == 2) and isinstance(idx[1], str):
			col = tuple(idx[1].split("."))
			if col in self._column_idxs:
				col = self._column_idxs[col]
		elif len(idx) == 3:
			if idx[1:] in self._column_idxs:
				col = self._column_idxs[idx[1:]]
		if col is None:
			return (None, None)
		
		return self._rows[row][col]
	
	def __iter__(self):
		
		for row in self._rows:
			yield row
	
	def __setitem__(self, idx, row):

		raise Exception("Impossible to alter a Query")
	
	def __delitem__(self, idx):

		raise Exception("Impossible to alter a Query")

