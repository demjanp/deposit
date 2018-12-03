from deposit.store.DLabel.DLabel import (DLabel)

from deposit.store.Conversions import (value_to_wkt)
import json

class DGeometry(DLabel):
	# constructor attributes:
	#	value: wkt or Literal or wktLiteral or [[x, y], ...]
	#	srid: EPSG code (int)
	#	srid_vertical: EPSG code (int)
	# public properties:
	#	value = wkt format
	#	type = geometry type in str format ("POINT", "POLYGON", etc.)
	#	coords = ([[x, y], ...], type); type = geometry type (POINT, POLYGON, etc.)
	#	srid
	#	srid_vertical
	#	prj: contents of ESRI prj file (str)
	# setters:
	#	set_prj(text)

	def __init__(self, value, srid = None, srid_vertical = None):
		# value = wktLiteral or Literal or wkt or [[x, y], ...]

		self._value, self._srid, self._srid_vertical = self.__convert_value(value, srid, srid_vertical)
		self._prj = None
		
		super(DGeometry, self).__init__(self._value)

	def __convert_value(self, value, srid, srid_vertical):

		return value_to_wkt(value, srid, srid_vertical)

	@property
	def query_value(self):
		# value to use when evaluating query

		return json.dumps(self._value)

	@property
	def srid(self):
		# SRID

		return -1 if self._srid is None else self._srid

	@property
	def srid_vertical(self):
		# vertical SRID

		return -1 if self._srid_vertical is None else self._srid_vertical

	@property
	def type(self):

		return self._value.split("(")[0].strip()

	@property
	def coords(self):
		# ([[x, y], ...], type); type = geometry type (POINT, POLYGON, etc.)

		try:
			return [[float(val) for val in point.strip().split(" ")] for point in self._value[self._value.rfind("(") + 1 : self._value.find(")")].split(",")], self._value.split("(")[0].upper()
		except:
			return [], None

	@property
	def prj(self):

		return self._prj
	
	def set_prj(self, text):

		self._prj = text
	
	def to_dict(self):

		return dict(
			dtype = "DGeometry",
			value = self._value,
			srid = self._srid,
			srid_vertical = self._srid_vertical,
			prj = self._prj,
		)

	def from_dict(self, data):

		self._value = data["value"]
		self._srid = data["srid"]
		self._srid_vertical = data["srid_vertical"]
		self._prj = data["prj"] if ("prj" in data) else None # DEBUG for compatibility with previous format
		
		return self
	
	def __str__(self):
		
		return "%s(%s)" % (self.__class__.__name__, self.type)
	
	def __repr__(self):

		value = self.__str__()
		if not value is None:
			value = value.encode("utf-8")
		return value

