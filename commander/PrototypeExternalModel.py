from deposit.commander.PrototypeListModel import PrototypeListModel
from deposit.DLabel import (DNone, DString, DGeometry)
import os

GEO_FIELD = "#Geometry"

class PrototypeExternalModel(PrototypeListModel):

	def __init__(self, parent_model, uri):
		
		self._uri = uri
		self._filename = None
		self._fields = [] # [name, ...]
		self._data = [] # [{column: DLabel, ...}, ...]; in order of rows
		
		super(PrototypeExternalModel, self).__init__(parent_model)
		
		self._filename = self._parent_model.store.resources.get_path(self._uri)[1]
	
	def set_data(self, data, fields, geometries = [], srid = -1):
		
		if geometries:
			self._fields = [GEO_FIELD] + fields
		else:
			self._fields = fields
		self._data = []
		for row in range(len(data)):
			self._data.append({})
			for column in data[row]:
				self._data[row][column] = DNone() if (data[row][column] is None) else DString(data[row][column])
		for row in range(len(geometries)):
			self._data[row] = dict([(0, DGeometry(geometries[row], srid))] + [(column + 1, self._data[row][column]) for column in self._data[row]])
	
	def uri(self):
		
		return self._uri
	
	def row_count(self):
		
		return len(self._data)
	
	def column_count(self):
		
		return len(self._fields)
	
	def column_headers(self):
		# return [name, ...]
		
		return self._fields
	
	def table_data(self, row, column):
		'''
		return dict(
			parent = class name,
			data = dict(
				row = row,
				column = column,
				value = data value or wkt,
				field = field,
				target = target,
				merge = True/False,
				geometry = True/False
				coords = [[x, y], ...], # if DGeometry
				srid = SRID code or -1,
			),
		)
		'''
		
		label = self._data[row][column]
		ret = dict(
			parent = self.__class__.__name__,
			data = dict(
				row = row,
				column = column,
				field = self._fields[column],
				target = self._fields[column],
				merge = False,
				value = label.value,
				geometry = False,
			)
		)
		if isinstance(label, DGeometry):
			ret["data"].update(dict(
				geometry = True,
				coords = label.coords[0],
				srid = label.srid,
			))
		return ret
