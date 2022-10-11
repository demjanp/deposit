import json
import datetime
import os
from urllib.parse import urlparse, urljoin
from urllib.request import pathname2url, url2pathname

if __name__ == "__main__":
	print()
	svalue = json.dumps(True)
	value = json.loads(svalue)
	print(svalue, value, type(value))
	svalue = json.dumps(1)
	value = json.loads(svalue)
	print(svalue, value, type(value))
	svalue = json.dumps(1.1)
	value = json.loads(svalue)
	print(svalue, value, type(value))
	svalue = json.dumps("2")
	value = json.loads(svalue)
	print(svalue, value, type(value))
	svalue = json.dumps(None)
	value = json.loads(svalue)
	print(svalue, value, type(value))
	print()
	print()
	
	# -----------------------------------------
	
	value = datetime.datetime.now()
	
	data = dict(
		dtype="DDateTime",
		value=value.isoformat(),
	)
	
	print(value, type(value))
	print()
	print(data)
	print()
	
	stored = json.dumps(data)
	
	print(stored)
	print()
	
	data = json.loads(stored)
	
	value = datetime.datetime.fromisoformat(data["value"])
	
	print(value, type(value))
	print()
	print()
	
	# -----------------------------------------
	
	value = "POLYGON((1 2, 1 4, 3 4, 3 2))"
	srid = 1234
	srid_vertical = 5678
	prj = "contents of ESRI prj file (str)"
	
	data = dict(
		dtype="DGeometry",
		value=value,
		srid=srid,
		srid_vertical=srid_vertical,
		prj=prj
	)
	
	print(value, type(value))
	print()
	print(data)
	print()
	
	stored = json.dumps(data)
	
	print(stored)
	print()
	
	data = json.loads(stored)
	
	value = data["value"]
	
	print(value, type(value))
	print()
	print()
	
	# -----------------------------------------
	
	path = '''c:\Program Files (x86)\Windows Multimedia Platform\sqmapi.dll'''
	# url = "https://picsum.photos/200"
	filename = "sqmapi.dll"
	
	value = urljoin("file:", pathname2url(path))
	# value = url
	
	A, B, C, D, E, F = 1, 2, 3, 4, 5, 6
	data = dict(
		dtype="DResource",
		value=value,
		filename=filename,
		path=None,
		projection="WKT string",
		worldfile=[A, D, B, E, C, F],
		image=True,
		location="WKT string"
	)
	
	stored = json.dumps(data)
	print(stored)
	print()
	
	data = json.loads(stored)
	
	parsed = urlparse(data["value"])
	path = url2pathname(parsed.path)
	print(parsed.scheme)
	print(path)
	print(os.path.isfile(path))
	
	# with urlopen(url) as response:
	# 	data = response.read()
	# print("DATA:", len(data))
	# print(path, type(path))
	# print(url, type(url))
	print()
