from urllib.parse import urlparse
import os

def get_worldfile(url):
	# try to retrieve worldfile parameters associated with image url
	
	parsed = urlparse(url)
	if parsed.scheme == "file":
		url = os.path.normpath(parsed.path.strip("/").strip("\\"))
	
	url = find_worldfile(url)
	if url is None:
		return None
	
	return load_worldfile(url)

def find_worldfile(url):
	# try to find and return path to worldfile associated with image uri
	
	path, ext = os.path.splitext(url)
	if not ext:
		return None
	ext = ext.strip(".").lower()
	for extw in ["%sw" % ext, "%swx" % ext, "%s%sw" % (ext[0], ext[-1]), "%s%swx" % (ext[0], ext[-1])]:
		path_worldfile = ".".join([path, extw])
		if os.path.isfile(path_worldfile):
			return path_worldfile
	return None

def load_worldfile(url):
	# load ESRI worldfile parameters from file
	# return A, D, B, E, C, F
	
	try:
		f = open(url, "r")
	except:
		return None
	lines = f.readlines()
	f.close()
	if len(lines) >= 6:
		try:
			lines = [float(line.replace(",",".")) for line in lines[:6]]
		except:
			return None
		return lines
	return None

def save_worldfile(params, path):
	# save worldfile complementary to path (path = the image file)
	# params = [A, D, B, E, C, F]
	
	path, ext = os.path.splitext(path)
	ext = ext.strip(".").lower()
	ext = "%s%sw" % (ext[0], ext[-1])
	path = ".".join([path, ext])
	f = open(path, "w")
	for value in params:
		f.write("%s\n" % (str(value).replace(".",",")))
	f.close()
	return path
	
