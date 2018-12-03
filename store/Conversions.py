from deposit.store.Namespaces import (OGC)
from urllib.parse import urlparse
from rdflib import (Literal)
import pathlib
import os


def id_to_int(id):

	return int(id.split("#")[0][4:]) if ("#" in id) else int(id[4:])

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
		wkt = ""
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

def wkt_to_wktLiteral(wkt, srid, srid_vertical):

	crs_string = "<http://www.opengis.net/def/crs/EPSG/0/%d>" % (-1 if srid is None else srid)
	if not srid_vertical is None:
		crs_string = "%s <http://www.opengis.net/def/crs/EPSG/0/%d>" % (crs_string, srid_vertical)
	return Literal("%s %s" % (crs_string, wkt), datatype = OGC.wktLiteral)

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

def as_url(value):
	# convert value to url
	
	if value is None:
		return value
	scheme = urlparse(value).scheme
	if (not scheme) or ((len(scheme) == 1) and scheme.isalpha()):
		return pathlib.Path(os.path.normpath(os.path.abspath(value))).as_uri()
	return value

def as_path(url):
	# convert file url to path
	
	parsed = urlparse(url)
	if parsed.scheme != "file":
		return None
	path = os.path.normpath(os.path.abspath(parsed.path.strip("/").strip("\\")))
	if os.path.isfile(path):
		return path
	return None

def to_unique(values):
	
	if not values:
		return []
	if len(values) == 1:
		return values
	values = sorted(values)
	if values[0] == values[-1]:
		return [values[0]]
	out = [values[i] for i in range(len(values) - 1) if values[i] != values[i+1]]
	if not out:
		return []
	if out[-1] != values[-1]:
		out.append(values[-1])
	return out