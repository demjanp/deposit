'''
	Deposit file store - OBJ
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as file.obj
'''

from urllib.parse import urlparse
import numpy as np
import os

class OBJ(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def get_extent(self, path):
		
		x_min, x_max = np.inf, -np.inf
		y_min, y_max = np.inf, -np.inf
		z_min, z_max = np.inf, -np.inf
		f = open(path, "r")
		coords_found = False
		while True:
			line = f.readline()
			if line.startswith("v "):
				coords_found = True
				x, y, z = [float(val) for val in line.split(" ")[1:]]
				x_min, x_max = min(x_min, x), max(x_max, x)
				y_min, y_max = min(y_min, y), max(y_max, y)
				z_min, z_max = min(z_min, z), max(z_max, z)
			elif coords_found:
				break
		f.close()
		return x_min, x_max, y_min, y_max, z_min, z_max
	
	def get_material(self, path, online = False):
		# return path_mtl, path_texture
		# TODO support for online store (http)
		
		if online:
			return None, None
		path_obj, filename = os.path.split(path)
		filename = filename.split(".")[0]
		path_mtl = os.path.join(path_obj, filename + ".mtl")
		if not os.path.isfile(path_mtl):
			path_mtl = None
		found = False
		for ext in [".jpg", ".jpeg", ".png"]:
			path_texture = os.path.join(path_obj, filename + ext)
			if os.path.isfile(path_texture):
				found = True
				break
		if not found:
			path_texture = None
		return path_mtl, path_texture
		
	