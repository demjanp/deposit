'''
	Deposit Label Classes
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	Interfaces to a Deposit store
'''

from deposit.DB import (OGC)
from rdflib import (URIRef, Literal)
from urllib.parse import urlparse
import numpy as np

def try_numeric(val):
	
	if val is None:
		return val
	out = None
	try:
		out = float(val)
	except:
		pass
	if out is None:
		if isinstance(val, bytes):
			return ""
		return val
	if out == int(out):
		return int(out)
	return out

def wktLiteral_to_wkt(geometry):
	# geometry: OGC.wktLiteral
	# return [wkt, srid, srid_vertical]
	
	geometry = str(geometry)
	if geometry.startswith("<http:"):
		srid_wkt = geometry.split(">")
		if len(srid_wkt) == 2:		
			srid, wkt = geometry.split(">")
			return wkt[1:], int(srid.split("/")[-1]), -1
		elif len(srid_wkt) == 3:
			srid, srid_vertical, wkt = srid_wkt
			return wkt[1:], int(srid.split("/")[-1]), int(srid_vertical.split("/")[-1])
	return geometry, None, None

def coords_to_wkt(coords):
	# coords: [[x, y], ...]
	# return wkt
	
	if len(coords) == 1:
		if len(coords[0]) == 2:
			return "POINT(%s %s)" % (coords[0][0], coords[0][1])
		else:
			return "POINTZ(%s %s %s)" % (coords[0][0], coords[0][1], coords[0][2])
	else:
		if len(coords[0]) == 2:
			typ = "POLYGON"
		else:
			typ = "POLYGONZ"
		return "%s((%s))" % (typ, ", ".join([" ".join([str(c) for c in coord]) for coord in coords]))

def wkt_to_coords(wkt):
	# return coordinates & type of geometry based on shape definition in WKT format
	# [[x, y, ...], ...], type; type = geometry type (POINT, POLYGON, etc.)
	
	return [[float(val) for val in point.strip().split(" ")] for point in wkt[wkt.rfind("(") + 1 : wkt.find(")")].split(",")], wkt.split("(")[0].upper()

def wkt_to_wktLiteral(wkt, srid, srid_vertical):
	
	crs_string = "<http://www.opengis.net/def/crs/EPSG/0/%d>" % (-1 if srid is None else srid)
	if not srid_vertical is None:
		crs_string = "%s <http://www.opengis.net/def/crs/EPSG/0/%d>" % (crs_string, srid_vertical)
	return Literal("%s %s" % (crs_string, wkt), datatype = OGC.wktLiteral)

def value_to_wkt(value, srid, srid_vertical):
	# attempt to convert value to a (wkt, srid) pair
	# value = wkt or Literal or wktLiteral or [[x, y], ...]
	# srid, srid_vertical = EPSG code (int)
	
	if not isinstance(srid, int):
		try:
			srid = int(srid)
		except:
			srid = None
	if not isinstance(srid_vertical, int):
		try:
			srid_vertical = int(srid_vertical)
		except:
			srid_vertical = None
	if isinstance(value, list):
		return coords_to_wkt(value), srid, srid_vertical
	_srid = None
	_srid_vertical = None
	if isinstance(value, Literal):
		if value.datatype == OGC.wktLiteral:
			wkt, _srid, _srid_vertical = wktLiteral_to_wkt(value)
			if _srid != -1:
				srid = _srid
			if _srid_vertical != -1:
				srid_vertical = _srid_vertical
		return wkt, srid, srid_vertical
		value = value.value
	wkt = str(value)
	if wkt.startswith("<http://www.opengis.net/def/crs/"):
		i = wkt.find(">")
		_srid = int(wkt[:i].split("/")[-1].strip())
		j = wkt.find(">", i + 1)
		if j > -1:
			_srid_vertical = int(wkt[i:j].split("/")[-1].strip())
			i = j
		wkt = wkt[i + 1:].strip()
		if _srid > -1:
			srid = _srid
		if (not _srid_vertical is None) and (_srid_vertical > -1):
			srid_vertical = _srid_vertical
	return wkt, srid, srid_vertical
	
def id_to_int(id):
	
	return int(id.split("#")[0][4:]) if ("#" in id) else int(id[4:])

def id_to_name(id):
	
	if "#" in id:
		id, ident = id.split("#")
		return ident.split("/")[-1] + ":" + id[4:]
	else:
		return id[4:]

class DLabel(object):
	
	def __init__(self, value, read_only = None, relation = None):
		
		self._value = value
		self._read_only = None
		self._relation = None
		
		if not read_only is None:
			self.set_read_only(read_only)
		if not relation is None:
			self.set_relation(relation)
	
	def __str__(self):
		
		return self._value
	
	def __repr__(self):
		
		value = self.__str__()
		if not value is None:
			value = value.encode("utf-8")
		return "%s: '%s'" % (self.__class__.__name__, value)
	
	@property
	def working(self):
		# working value (for evaluating queries)
		
		return None
	
	@property
	def value(self):
		# string format
		
		return self._value

	@property
	def label(self):
		# Literal(value)
		
		return Literal(self._value)

	@property
	def read_only(self):
		# True / False
		
		return self._read_only
	
	def set_read_only(self, state):
		
		if (state is None) or isinstance(state, bool):
			self._read_only = state
		elif isinstance(state, np.bool_):
			self._read_only = bool(state)
		elif isinstance(state, str):
			if state == "True":
				self._read_only = True
			elif state == "False":
				self._read_only = False
	
	@property
	def relation(self):
		# id_rel or None
		
		return self._relation
	
	def set_relation(self, id_rel):
		
		self._relation = id_rel
	
class DString(DLabel):
	# constructor attributes:
	#	value: str compatible type or Literal
	#	read_only: True / False
	#	relation: id_rel or None
	# public properties:
	#	value = string format
	#	label = Literal(value)
	#	working = working value (for evaluating queries)
	
	def __init__(self, value, read_only = None, relation = None):
		
		self._value = self.__convert_value(value)
		self._working = self._value # working value (for evaluating queries)
		
		super(DString, self).__init__(self._value, read_only, relation)
	
	def __convert_value(self, value):
		
		if isinstance(value, Literal):
			value = value.value
		return str(value)
	
	@property
	def working(self):
		# working value (for evaluating queries)
		
		return self._working
	
	def set_working(self, value):
		
		self._working = value

class DDateTime(DLabel):
	
	def __init__(self, value, read_only = None, relation = None):
		
		self._value = self.__convert_value(value)
		self._working = self._value # working value (for evaluating queries)
		
		super(DDateTime, self).__init__(self._value, read_only, relation)
	
	def __convert_value(self, value):
		
		return str(value)

	@property
	def working(self):
		# working value (for evaluating queries)
		
		return self._working

	def set_working(self, value):
		
		self._working = value

class DResource(DString):
	# constructor attributes:
	#	value: str compatible type or URIRef or Literal
	#	read_only: True / False
	#	relation: id_rel or None
	# public properties:
	#	value = string format
	#	label = URIRef(value)
	#	working = None
	
	def __init__(self, value, read_only = None, relation = None):
		
		super(DResource, self).__init__(value, read_only, relation)
	
	@property
	def working(self):
		# None
		
		return None

	@property
	def label(self):
		# URIRef(value)
		
		return URIRef(self._value)

class DGeometry(DLabel):
	# constructor attributes:
	#	value: wkt or Literal or wktLiteral or [[x, y], ...]
	#	srid: EPSG code (int)
	#	srid_vertical: EPSG code (int)
	#	read_only: True / False
	#	relation: id_rel or None
	# public properties:
	#	value = wkt format
	#	label = wktLiteral(value)
	#	coords = ([[x, y], ...], type); type = geometry type (POINT, POLYGON, etc.)
	#	srid
	#	srid_vertical
	#	working = None
	
	def __init__(self, value, srid = None, srid_vertical = None, read_only = None, relation = None):
		# value = wktLiteral or Literal or wkt or [[x, y], ...]
		
		self._value, self._srid, self._srid_vertical = self.__convert_value(value, srid, srid_vertical)
		
		super(DGeometry, self).__init__(self._value, read_only, relation)
	
	def __convert_value(self, value, srid, srid_vertical):
		
		return value_to_wkt(value, srid, srid_vertical)
	
	@property
	def label(self):
		# wktLiteral(value)
		
		return wkt_to_wktLiteral(self._value, self._srid, self._srid_vertical)
	
	@property
	def srid(self):
		# SRID
		
		return -1 if self._srid is None else self._srid
	
	@property
	def srid_vertical(self):
		# vertical SRID
		
		return -1 if self._srid_vertical is None else self._srid_vertical
	
	@property
	def coords(self):
		# ([[x, y], ...], type); type = geometry type (POINT, POLYGON, etc.)
		
		try:
			return wkt_to_coords(self._value)
		except:
			return [], None

class DNone(DLabel):
	# public properties:
	#	value = None
	#	label = Literal()
	#	working = None
	
	def __init__(self, read_only = None, relation = None):
		
		super(DNone, self).__init__(None, read_only, relation)

	@property
	def value(self):
		# None
		
		return None

	@property
	def label(self):
		# Literal()
		
		return Literal()

	def __str__(self):
		
		return ""
