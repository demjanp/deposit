import json

def add_srid_to_wkt(wkt, srid, srid_vertical):
	
	if (srid_vertical is not None) and (srid_vertical > -1):
		wkt = ("VERT_SRID=%d;" % (srid_vertical)) + wkt
	if (srid is not None) and (srid > -1):
		wkt = ("SRID=%d;" % (srid)) + wkt
	return wkt

def split_srid_from_wkt(wkt):
	
	def _extract_srid(substr, prefix):
		
		srid = None
		if substr.startswith(prefix):
			i = substr.find(";")
			if i == -1:
				raise Exception("Error in WKT: %s" % (substr))
			srid = int(substr[:i-1].split("=")[1].strip())
			substr = substr[i+1:]
		return srid, substr
	
	srid, wkt = _extract_srid(wkt.strip(), "SRID")
	srid_vertical, wkt = _extract_srid(wkt, "VERT_SRID")
	
	return wkt, srid, srid_vertical

def get_coords_properties(coords):
	
	ndims = 1
	ncoords = len(coords)
	c = coords[0]
	while isinstance(c, list):
		ncoords = len(c)
		c = c[0]
		ndims += 1
	
	return ndims, ncoords

def get_ndims_required(geom_type):
	
	geom_type_ = geom_type.upper().rstrip("Z").rstrip("M")
	
	lookup = {
		"POINT": 1,
		"MULTIPOINT": 2,
		"LINESTRING": 2,
		"POLYGON": 3,
		"MULTIPOLYGON": 4,
	}
	if geom_type_ not in lookup:
		raise Exception("Invalid geometry type: %s" % (geom_type))
	
	return lookup[geom_type_]
	

def coords_to_wkt(geom_type: str, coords: list, srid: int = None, srid_vertical: int = None) -> str:
	
	def _to_list(crds):
		
		for i in range(len(crds)):
			if isinstance(crds[i], tuple):
				crds[i] = list(crds[i])
			if isinstance(crds[i], list):
				_to_list(crds[i])
	
	def _close_polygons(crds):
		
		if not isinstance(crds[0], list):
			return
		if isinstance(crds[0][0], list):
			for crd in crds:
				_close_polygons(crd)
		elif crds[0] != crds[-1]:
			crds.append(crds[0])
	
	def _points_to_wkt(points):
		
		return "(%s)" % (", ".join([" ".join([str(val) for val in point]) for point in points]))
	
	def _polygon_to_wkt(polygon):
		
		return "(%s)" % ", ".join([_points_to_wkt(points) for points in polygon])
	
	if not coords:
		return None
	
	_to_list(coords)
	
	geom_type = geom_type.upper()
	is_z = geom_type.endswith("Z")
	is_m = geom_type.endswith("M")
	if is_z:
		geom_type = geom_type.rstrip("Z")
	if is_m:
		geom_type = geom_type.rstrip("M")
	ndims, ncoords = get_coords_properties(coords)
	if is_z and ncoords != 3:
		raise Exception("Invalid number of coordinates (%d). Required: 3." % (ncoords))
	if is_m and ncoords != 4:
		raise Exception("Invalid number of coordinates (%d). Required: 4." % (ncoords))
	is_z = (ncoords == 3)
	is_m = (ncoords == 4)
	
	ndims_required = get_ndims_required(geom_type)
	
	if ndims != ndims_required:
		raise Exception("Invalid number of dimensions (%d) for geometry type %s. Required: %d." % (ndims, geom_type, ndims_required))
	
	if geom_type.endswith("POLYGON"):
		_close_polygons(coords)
	
	if is_z:
		geom_type += "Z"
	elif is_m:
		geom_type += "M"
	
	wkt = geom_type
	if ndims == 1:
		wkt += "(%s)" % (" ".join([str(val) for val in coords]))
	elif ndims == 2:
		wkt += _points_to_wkt(coords)
	elif ndims == 3:
		wkt += _polygon_to_wkt(coords)
	elif ndims == 4:
		wkt += "(%s)" % ", ".join([_polygon_to_wkt(polygon) for polygon in coords])
	
	wkt = add_srid_to_wkt(wkt, srid, srid_vertical)
	
	return wkt

def wkt_to_coords(wkt):
	# returns (geometry_type, coordinates, srid, srid_vertical)
	
	def _extract_srid(substr, prefix):
		
		srid = None
		if substr.startswith(prefix):
			i = substr.find(";")
			if i == -1:
				raise Exception("Error in WKT: %s" % (substr))
			srid = int(substr[:i-1].split("=")[1].strip())
			substr = substr[i+1:]
		return srid, substr
	
	wkt = wkt.strip()
	wkt = wkt.replace("(","[")
	wkt = wkt.replace(")","]")
	
	wkt, srid, srid_vertical = split_srid_from_wkt(wkt)
	
	i = wkt.find("[")
	geometry_type = wkt[:i].strip().upper()
	wkt = wkt[i:]
	
	collect = ""
	while True:
		j = wkt.find(",")
		if j == -1:
			j = wkt.find("]")
		if j > -1:
			substr = wkt[:j]
			i = substr.find("[")
			collect += wkt[:i+1]
			substr = ",".join([item.strip() for item in wkt[i+1:j].strip().split(" ")])
			if substr:
				collect += "[%s]" % (substr)
			collect += wkt[j]
			wkt = wkt[j+1:]
		else:
			break
	if collect:
		wkt = collect + wkt
	coords = json.loads(wkt)
	
	if geometry_type.startswith("POINT"):
		coords = coords[0]
	
	return geometry_type, coords, srid, srid_vertical

