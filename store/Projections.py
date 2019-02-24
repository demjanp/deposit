import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import os

# TODO fix this
def get_raster_projection(url):
	# try to retrieve projection wkt from raster file
	# return wkt in str format or None
	
	parsed = urlparse(url)
	if parsed.scheme == "file":
		url = os.path.normpath(parsed.path.strip("/").strip("\\"))
	if not os.path.isfile(url):
		return None
	path_aux = None
	for suffix in [".aux.xml", ".AUX.XML"]:
		if os.path.isfile(url + suffix):
			path_aux = url + suffix
			break
	wkt = None
	if path_aux:
		tree = ET.parse(path_aux)
		for item in tree.findall("SRS"):
			wkt = item.text
			break
	return wkt

# TODO fix this
def save_raster_projection(wkt, path):
	# save projection complementary to path (path = the image file)
	
	path, ext = os.path.splitext(path)
	path = ".".join([path, "aux.xml"])
	f = open(path, "w")
	f.write("<PAMDataset><SRS>%s</SRS></PAMDataset>" % (wkt))
	f.close()
	return path

def get_esri_prj(url):
	# try to retrieve contents of esri prj file associated with shapefile
	
	parsed = urlparse(url)
	if parsed.scheme == "file":
		url = os.path.normpath(parsed.path.strip("/").strip("\\"))
	
	path, ext = os.path.splitext(url)
	if ext.lower() != ".shp":
		return None
	if not os.path.isfile(url):
		return None
	for extp in ["prj", "PRJ"]:
		path_prj = ".".join([path, extp])
		if os.path.isfile(path_prj):
			with open(path_prj, "r") as f:
				text = f.read()
			return text
	return None
	
