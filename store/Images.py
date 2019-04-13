from deposit.DModule import (DModule)

from PySide2 import (QtCore, QtGui, QtSvg)
from PIL import Image
import hashlib
import shutil
import imghdr
import sys
import os

class Images(DModule):
	
	IMAGE_EXTENSIONS = ["svg", "png", "jpg", "jpeg", "gif", "tif", "tiff", "bmp"]
	
	def __init__(self, store):
		
		self.store = store
		self._thumbnails = {} # {thumb_filename: path, ...}; thumb_filename = [hashed uri].[ext]

		DModule.__init__(self)
	
	def get_format(self, source):
		# return format (extension) of local image file or None if not recognized
		
		if isinstance(source, str):
			ext = os.path.splitext(source)[-1].lower()[1:]
			if ext in self.IMAGE_EXTENSIONS:
				return ext
			return None
		try:
			return imghdr.what(source)
		except:
			print("Images.get_format", sys.exc_info())
		return None
	
	def make_thumbnail(self, src_path, tgt_path, size, src_format):
		# generate a thumbnail
		
		stat = os.stat(src_path)
		ta, tm = stat.st_atime, stat.st_mtime
		
		if src_format == "svg":
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
			try:
				icon = Image.open(src_path).convert("RGB")
			except:
				return
			icon.thumbnail((size, size), Image.ANTIALIAS)
			icon.save(tgt_path, quality = 100)
			icon.close()
		
		os.utime(tgt_path, (ta, tm))
	
	def get_thumbnail(self, label, size = 256, local_folder = None):
		# find or make thumbnail from image specified by label (DResource)
		# return path
		
		if local_folder is None:
			local_folder = self.store.local_folder
		if not local_folder:
			return None
		
		# thumbnail filename
		filename = "%s_%s.jpg" % (hashlib.md5(label.value.encode("utf-8")).hexdigest(), size)
		
		tm_orig = label.time_modified
		
		if filename in self._thumbnails:
			# check if thumbnails modified time matches the source file
			if tm_orig > -1:
				if tm_orig == os.stat(self._thumbnails[filename]).st_mtime:
					return self._thumbnails[filename]
		
		local_folder = os.path.join(local_folder, "_thumbnails")
		if not os.path.exists(local_folder):
			os.makedirs(local_folder)
		tgt_path = os.path.join(self.store.files.get_new_dir(local_folder), filename)
		
		src_format = self.get_format(label.filename)
		if src_format is None:
			f_src = label.open()
			src_format = self.get_format(f_src)
			f_src.close()
			if src_format is None:
				return None
			src_filename = "thumbnail.%s" % (src_format)
		else:
			src_filename = label.filename
		
		src_path = os.path.join(self.store.files.get_temp_path(), src_filename)
		
		# make temporary copy of image
		f_src = label.open()
		if f_src is None:
			return None
		f_tgt = open(src_path, "wb")
		shutil.copyfileobj(f_src, f_tgt)
		f_src.close()
		f_tgt.close()
		
		if tm_orig > -1:
			# set copys modified time to the originals
			ta = os.stat(src_path).st_atime
			os.utime(src_path, (ta, tm_orig))
		
		# generate new thumbnail
		self.make_thumbnail(src_path, tgt_path, size, src_format)
		
		self._thumbnails[filename] = tgt_path
		
		return tgt_path
		
	def load_thumbnails(self, local_folder = None):
		
		if local_folder is None:
			local_folder = self.store.local_folder
		if not local_folder:
			return
		local_folder = os.path.join(local_folder, "_thumbnails")
		if os.path.exists(local_folder):
			for dirname in os.listdir(local_folder):
				dirname = os.path.join(local_folder, dirname)
				if os.path.isdir(dirname):
					for filename in os.listdir(dirname):
						self._thumbnails[filename] = os.path.abspath(os.path.join(dirname, filename))

