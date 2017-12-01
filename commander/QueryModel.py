from deposit.commander.PrototypeListModel import PrototypeListModel
from deposit.DLabel import (DResource, DGeometry, id_to_name)
import os

class QueryModel(PrototypeListModel):
	
	def __init__(self, parent_model, query, relation = None, cls_id = None):
		
		self._relation = relation # [obj_id, rel_label, cls_label, cls_id, reversed]
		self._cls_id = cls_id
		self._query = None
		self._query_str = query
		self._images = [] # [[row, column], ...]; row, column: indexes in self._query
		self._geometries = [] # [[row, column], ...]; row, column: indexes in self._query
		
		super(QueryModel, self).__init__(parent_model)
		
		if (not self._cls_id is None) and ("." in self._cls_id):
			self._cls_id = self._cls_id.split(".")[1]
		
		self._query = self._parent_model.query(query, self._relation, self._cls_id)
	
	def set_images(self, images):
		# set by QueryLstView after populating (to only load once)
		
		self._images = images
		self._view.update_tabs_enabled()
	
	def has_images(self):
		
		return len(self._images) > 0
	
	def has_geometry(self):
		
		return len(self._geometries) > 0
	
	def has_relation(self):
		
		return (not self._relation is None)
	
	def query_str(self):
		
		return self._query_str
	
	def parent_class(self):
		
		return self._cls_id
	
	def relation(self):
		
		if not self._relation is None:
			return dict(
				obj_id2 = self._relation[0],
				rel_label = self._relation[1],
				reversed = self._relation[4],
			)
		return {}
	
	def row_count(self):
		
		return len(self._query.objects)
	
	def column_count(self):
		
		return len(self._query.columns)
	
	def column_headers(self):
		
		return [[column[0], column[1].value] for column in self._query.columns]
	
	def objects(self):
		
		return self._query.objects
	
	def classes(self):
		
		classes = []
		for column in self._query.columns:
			for cls_id in column[0].split("."):
				classes.append(cls_id)
		if self._cls_id and not self._cls_id in classes:
			classes.append(self._cls_id)
		return classes
	
	def object_classes(self, obj_id):
		# return [[cls_id, label], ...]
		
		return [[cls_id, self._parent_model.store.get_label(cls_id).value] for cls_id in self._parent_model.store.members.get_parents(obj_id)]
	
	def object_relations(self):
		# return [[rel label, cls label, cls_id, reversed], ...]
		
		relations = self._parent_model.store.relations.get_multi(self._query.keys())
		return sorted(relations, key = lambda row: [-1 if (row[2] is None) else self._parent_model.store.get_order(row[2]), row[0], row[3]])
	
	def image_count(self):
		
		return len(self._images)
	
	def images(self):
		
		return self._images
	
	def update_data(self, data):
		# data = [[row, cls_id, obj_id, value], ...]
		
		self._parent_model.store.begin_change()
		obj_lookup = {} # {row: obj_id, ...}
		for row, cls_id, obj_id, value in data:
			if obj_id is None:
				if row in obj_lookup:
					obj_id = obj_lookup[row]
				elif self._cls_id and value:
					obj_id = self._parent_model.store.objects.add()
					self._parent_model.store.members.add(self._cls_id, obj_id)
					obj_lookup[row] = obj_id
			if obj_id:
				self._parent_model.store.relations.add_descriptor(cls_id, obj_id, value)
		self._parent_model.store.end_change()
	
	def set_data(self, item_data, value):
		
		if value == "":
			value = None
		if item_data["data"]["value"] == value:
			return
		if value is None:
			if not item_data["data"]["rel_id"] is None:
				self._parent_model.store.relations.remove(item_data["data"]["rel_id"])
		elif ("obj_id" in item_data["data"]) and ("cls_id" in item_data["data"]):
			obj_id = item_data["data"]["obj_id"]
			cls_id = item_data["data"]["cls_id"]
			self._parent_model.store.relations.add_descriptor(cls_id, obj_id, value)
	
	def object_data(self, row):
		'''
		return dict(
			parent = "QueryModel",
			data = dict(
				obj_id = obj_id,
				row = row,
				value = int(obj_id)
				
				obj_id2 = obj_id (related),
				rel_label = label,
				reversed = True/False,
				parent_class = cls_id
			),
		)
		'''
		
		ret = dict(parent = self.__class__.__name__, data = {})
		if not self.has_store():
			return ret
		if not self._relation is None:
			ret["data"] = dict(
				obj_id2 = self._relation[0],
				rel_label = self._relation[1],
				reversed = self._relation[4],
			)
		if not self._cls_id is None:
			ret["data"]["parent_class"] = self._cls_id
		ret["data"]["row"] = row
		if row < len(self._query.objects):
			ret["data"].update(dict(
				obj_id = self._query.objects[row],
				value = id_to_name(self._query.objects[row]),
			))
		return ret
	
	def table_data(self, row, column):
		'''
		return dict(
			parent = "Query",
			data = dict(
				obj_id = obj_id,
				row = row,
				column = column,
				cls_id = cls_id,
				rel_id = rel_id,
				value = value,
				read_only = True/False,
				geometry = True/False
				image = True/False
				obj3d = True/False
				storage_type = Resources.RESOURCE_STORED / _LOCAL / _ONLINE / _CONNECTED_LOCAL / _CONNECTED_ONLINE
				obj_id2 = obj_id (related),
				rel_label = label,
				reversed = True/False,
			),
		)
		'''
		
		ret = self.object_data(row)
		
		if not self.has_store():			
			return ret
		
		if "obj_id" in ret["data"]:
			obj_id = ret["data"]["obj_id"]
		else:
			return ret
		
		cls_id, cls_label = self._query.columns[column]
		value = self._query[obj_id][cls_id]
		cls_id = cls_id.split(".")[-1]
		read_only = value.read_only
		if ("#" in obj_id) or (value.relation and ("#" in value.relation)):
			read_only = True
		geometry = isinstance(value, DGeometry)
		ret["data"].update(dict(
			column = column,
			cls_id = cls_id,
			rel_id = value.relation,
			value = value.value,
			read_only = read_only,
			geometry = isinstance(value, DGeometry),
		))
		if geometry:
			ret["data"]["coords"] = value.coords
		
		image = False
		obj3d = False
		storage_type = 0
		if isinstance(value, DResource):
			uri = value.value
			storage_type = self._parent_model.store.resources.get_storage_type(uri)
			image = self._parent_model.store.resources.is_image(uri)
			if not image:
				obj3d = self._parent_model.store.resources.is_3d(uri)
		ret["data"].update(dict(
			image = image,
			obj3d = obj3d,
			storage_type = storage_type,
		))
		if not self._relation is None:
			ret["data"].update(dict(
				obj_id2 = self._relation[0],
				rel_label = self._relation[1],
				reversed = self._relation[4],
			))
		
		return ret
	
	def image_data(self, row):
		
		if row < len(self._images):
			return self._images[row]
	
	def is_url_image(self, url):
			
		return self._parent_model.store.resources.is_external_image(url)
	
	def get_affected_rows(self, ids):
		
		rows = []
		if self._query.objects:
			for obj_id in ids:
				try:
					row = self._query.objects.index(obj_id)
				except:
					row = -1
				if row > -1:
					rows.append(row)
		return rows
	
	def get_affected_cells(self, ids):
		# find rows and columns with supplied obj and cls ids
		# return [[row, column], ...]
		
		rows = self.get_affected_rows(ids)
		columns = []
		if self._query.columns:
			descriptors = [column[0].split(".")[-1] for column in self._query.columns]
			for cls_id in ids:
				try:
					column = descriptors.index(cls_id)
				except:
					column = -1
				if column > -1:
					columns.append(column)
		ret = []
		if rows and columns:
			for row in rows:
				for column in columns:
					ret.append([row, column])
		return ret
	

