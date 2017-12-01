'''
	Deposit file store - Shapefiles
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as file.shapefiles
'''

WKT_PREFIXES = {
	"POINT(": 1,
	"LINESTRING(": 3,
	"POLYGON(": 5,
	"MULTIPOINT(": 8,
	"POINTZ(": 11,
	"LINESTRINGZ(": 13,
	"POLYGONZ(": 15,
	"MULTIPOINTZ(": 18,
	"POINTM(": 21,
	"LINESTRINGM(": 23,
	"POLYGONM(": 25,
	"MULTIPOINTM(": 28,
}

import os
import shutil
import numpy as np
from shapefile import (Reader, Writer)
from deposit.DLabel import (try_numeric, wkt_to_coords)

def _stringify(value):
	# sanitize value to string if no type known to Deposit
	# TODO make obsolete by implementing types other than str and OGC.wktLiteral
	
	if not (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)):
		return str(value)
	return value

class Shapefiles(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def is_shapefile(self, path):
		# return True if path is a shapefile (has a shapefile extension)
		
		return (os.path.splitext(path)[-1].lower() == ".shp")
		
	def get_data(self, path):
		# return geometries, srid, fields, data
		# geometries: [wkt, ...]
		# srid: epsg code
		# fields: [name, ...]
		# data: [{column: value, ...}, ...]
		# TODO support remotely stored files
		# TODO load projection from prj file
		
		def _get_points(shape):
			
			points = shape.points
			if hasattr(shape, "z"):
				return np.vstack((np.array(points).T, shape.z)).T.tolist()
			return points
		
		# get SRID
		srid = -1
		prj_path = path[:-3] + "prj"
		if os.path.isfile(prj_path):
			pass # TODO
		
		# get geometries & data
		sf = Reader(path)
		fields = [f[0] for f in sf.fields[1:]]
		shp_type = sf.shape(0).shapeType
		shapes_wkt = { # WKT formatting for geometric shapes
			1: "POINT(%s)",
			3: "LINESTRING(%s)",
			5: "POLYGON((%s))",
			8: "MULTIPOINT(%s)",
			11: "POINTZ(%s)",
			13: "LINESTRINGZ(%s)",
			15: "POLYGONZ((%s))",
			18: "MULTIPOINTZ(%s)",
			21: "POINTM(%s)",
			23: "LINESTRINGM(%s)",
			25: "POLYGONM((%s))",
			28: "MULTIPOINTM(%s)",
		}
		if not shp_type in shapes_wkt:
			raise Exception("Unrecognized shapefile type")
		
		geometries = [shapes_wkt[shp_type] % ", ".join([" ".join([str(p) for p in point]) for point in _get_points(shape)]) for shape in sf.shapes()]
		# geometries = [wkt definition, ...] in order of records
		data = [dict([(i, _stringify(try_numeric(record[i]))) for i in range(len(fields))]) for record in sf.records()]
		# data = [{column: value, ...}, ...]
		
		return geometries, srid, fields, data

	def write(self, path, geometries, srid, fields = [], data = []):
		# create a shapefile
		# geometries: [wkt, ...]
		# srid: epsg code
		# fields: [name, ...]
		# data: [{field: value, ...}, ...]
		# TODO srid
		
		def _abbrev_to(name, chars, fields_abbrev):
			
			if len(name) > chars:
				n = 1
				while True:
					name_new = name[:chars - len(str(n))] + str(n)
					if not name_new in fields_abbrev.values():
						return name_new
					n += 1
			return name
		
		if data and (len(geometries) != len(data)):
			raise Exception("Numbers of geometries and data rows must match")
		fields_abbrev = {} # {field: field_abbrev, ...}; abbreviated field names
		for field in fields:
			field_abbrev = field
			if len(field_abbrev) > 10:
				if "." in field_abbrev:
					field_abbrev = field_abbrev.split(".")
					field_abbrev = "_".join([_abbrev_to(field_abbrev[0], 4, fields_abbrev), _abbrev_to(field_abbrev[1], 5, fields_abbrev)])
				else:
					field_abbrev = _abbrev_to(field_abbrev, 10, fields_abbrev)
			field_abbrev = field_abbrev.replace(".", "_")
			fields_abbrev[field] = field_abbrev
		shapeType = -1
		for wkt in geometries:
			for s in WKT_PREFIXES:
				if wkt.startswith(s):
					if shapeType > -1:
						if WKT_PREFIXES[s] != shapeType:
							raise Exception("Geometries must be of the same type")
					else:
						shapeType = WKT_PREFIXES[s]
					break
		sf = Writer(shapeType = shapeType)
		columns = []
		types = {} # {column: type, ...}
		shp_types = {bool: "C", int: "N", float: "N", str: "C"}
		conv_order = ["N", "C"]
		for row in data:
			for col in row:
				if not col in columns:
					columns.append(col)
				typ = type(row[col])
				typ = shp_types[typ] if typ in shp_types else "C"
				if (not col in types) or ((typ != types[col]) and (conv_order.index(typ) > conv_order.index(types[col]))):
					types[col] = typ
		columns = sorted(columns)
		if not fields:
			fields = columns
		for field in fields:
			sf.field(fields_abbrev[field], fieldType = types[field], size = "128")
		for i in range(len(geometries)):
			coords, _ = wkt_to_coords(geometries[i])
			if shapeType in [1, 11, 21]: # point types
				sf.point(*coords[0], shapeType = shapeType)
			else:
				sf.poly(shapeType = shapeType, parts = [coords])
			if data:
				sf.record(*[(data[i][field] if field in data[i] else None) for field in fields])
		sf.save(path)
		
		# try to find prj file for srid
		if srid > -1:
			src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "prj", "%d.prj" % (srid)))
			if os.path.isfile(src_path):
				shutil.copyfile(src_path, "%s.prj" % (os.path.splitext(path)[0]))
