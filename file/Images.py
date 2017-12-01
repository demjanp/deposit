'''
	Deposit file store - Images
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as file.images
'''

import os
import sys
import json
from rdflib import URIRef
from PyQt5 import (QtCore, QtGui, QtSvg)
import imghdr
import shutil
import tempfile
from PIL import Image
from urllib.request import urlopen
from urllib.parse import urlparse

class Images(object):
	
	IMAGE_EXTENSIONS = ["svg", "png", "jpg", "jpeg", "gif", "tif", "tiff", "bmp"]
	
	def __init__(self, store):
		
		self.__file = store
	
	def __getattr__(self, key):
		
		return getattr(self.__file, key)
	
	def get_format(self, path):
		# return format (extension) of local image file or None if not recognized
		
		ext = os.path.splitext(path)[-1].lower()[1:]
		if not ext in self.IMAGE_EXTENSIONS:
			return None
		if ext == "svg":
			return ext
		try:
			return imghdr.what(path)
		except:
			print("Images.get_format", sys.exc_info())
		
		return None
	
	def make_thumbnail(self, src_path, tgt_path, size):
		# generate a thumbnail
		
		format = self.get_format(src_path)
		if not format:
			return
		
		if format == "svg":
			renderer = QtSvg.QSvgRenderer(src_path)
			rnd_size = renderer.defaultSize()
			rw, rh = rnd_size.width(), rnd_size.height()
			scale = max(rw / size, rh / size)
			w, h = int(round(rw / scale)), int(round(rh / scale))
			pixmap = QtGui.QPixmap(w, h)
			pixmap.fill(QtCore.Qt.white)
			painter = QtGui.QPainter(pixmap)
			renderer.render(painter)
			pixmap.save(tgt_path)
			painter.end()
		else:
			icon = Image.open(src_path).convert("RGB")
			icon.thumbnail((size, size), Image.ANTIALIAS)
			icon.save(tgt_path, quality = 100)
			icon.close()
		
		# add format information to thumbnail file
		f = open(tgt_path, "a+b")
		f.write(b"\xff\xfe%b" % (format.encode("ascii")))
		f.close()
	
