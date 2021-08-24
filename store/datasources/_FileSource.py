from deposit import Broadcasts, __version__
from deposit.store.datasources._DataSource import (DataSource)
from deposit.store.Conversions import (as_url)

from urllib.parse import urlparse
import datetime, time
import shutil
import sys
import os

class FileSource(DataSource):

	def __init__(self, store, url = None):

		DataSource.__init__(self, store)
		
		self.set_url(url)
	
	def set_url(self, url):
		
		if url is None:
			self.url = None
			self.identifier = None
		else:
			self.url = url
			self.identifier = os.path.splitext(self.url)[0] + "#"
		if self.store.data_source == self:
			self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)
	
	def load_file(self, path):
		# override
		
		return {}
	
	def save_file(self, data, path):
		# override
		
		pass
	
	def load(self):
		
		if self.url is None:
			return False
		
		self.stop_broadcasts()
		self.store.events.stop_recording()
		self.store.clear()
		
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//").replace("%20"," ")))
		
		data = None
		if not os.path.isfile(path):
			self.save()
		if not self.wait_if_busy():
			return False
		self.is_busy = True
		try:
			data = self.load_file(path)
		except:
			print("LOAD ERROR: %s" % (str(sys.exc_info())))
			self.is_busy = False
			return False
		
		for name in ["classes", "objects", "changed"]:
			if name not in data:
				self.is_busy = False
				return False
		
		self.store.local_folder = os.path.split(path)[0]
		
		for id in data["objects"]:
			for name in data["objects"][id]["descriptors"]:
				if (data["objects"][id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data["objects"][id]["descriptors"][name]["label"]["path"] is None):
					path = data["objects"][id]["descriptors"][name]["label"]["path"]
					path, fname = os.path.split(path)
					path = os.path.split(path)[1]
					data["objects"][id]["descriptors"][name]["label"]["value"] = as_url(os.path.join(self.store.local_folder, path, fname))
					data["objects"][id]["descriptors"][name]["label"]["path"] = os.path.join(self.store.local_folder, path, fname)
		
		self.store.classes.from_dict(data["classes"])
		self.store.objects.from_dict(data["objects"])

		has_class_descriptors = False  # TODO will be obsolete for new databases
		for name in data["classes"]:
			has_class_descriptors = ("descriptors" in data["classes"][name])
			break
		
		resource_uris = []
		for id in data["objects"]:
			for name in data["objects"][id]["descriptors"]:
				if (data["objects"][id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data["objects"][id]["descriptors"][name]["label"]["path"] is None):
					if not data["objects"][id]["descriptors"][name]["label"]["value"] in resource_uris:
						resource_uris.append(data["objects"][id]["descriptors"][name]["label"]["value"])
		self.store.set_local_resource_uris(resource_uris)
		if not has_class_descriptors:  # TODO will be obsolete for new databases
			self.store.populate_descriptor_names()  # TODO will be obsolete for new databases
			self.store.populate_relation_names()  # TODO will be obsolete for new databases

		self.store.changed = data["changed"]
		
		if "events" in data:  # TODO will be obsolete for new databases
			self.store.events.from_list(data["events"])
		
		if "user_tools" in data:  # TODO will be obsolete for new databases
			self.store.user_tools.from_list(data["user_tools"])
		
		if "queries" in data:  # TODO will be obsolete for new databases
			self.store.queries.from_dict(data["queries"])
		
		self.store.images.load_thumbnails()
		
		self.store.set_datasource(self)
		
		self.is_busy = False
		
		self.store.events.resume_recording()
		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)
		
		return True

	def save(self):
		
		if self.url is None:
			return False
		
		if not self.wait_if_busy():
			return False
		self.is_busy = True
		
		data = dict(
			classes = self.store.classes.to_dict(), # {name: class data, ...}
			objects = self.store.objects.to_dict(), # {id: object data, ...}
			changed = self.store.changed,
			events = self.store.events.to_list() if self.store.save_events else [],
			user_tools = self.store.user_tools.to_list(),
			queries = self.store.queries.to_dict(),
			deposit_version = __version__,
		)
		
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//").replace("%20"," ")))
		
		saved_path = os.path.join(self.store.files.get_temp_path(), os.path.split(path)[1])
		self.save_file(data, saved_path)
		
		if os.path.isfile(path):
			back_path = self.store.files.get_backup_path()
			tgt_file, ext = os.path.splitext(os.path.split(path)[1])
			tgt_file = "%s_%s" % (tgt_file, datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d'))
			n = 1
			while True:
				tgt_path = os.path.join(back_path, "%s_%d%s" % (tgt_file, n, ext))
				if not os.path.isfile(tgt_path):
					break
				n += 1
			shutil.move(path, os.path.join(back_path, tgt_path))
		
		tgt_dir = os.path.split(path)[0]
		if not os.path.isdir(tgt_dir):
			os.mkdir(tgt_dir)
		shutil.move(saved_path, path)
		
		new_local_folder = os.path.split(path)[0]
		if new_local_folder != self.store.local_folder:
			self.store.set_local_folder(new_local_folder)
		
		self.is_busy = False
		
		if not os.path.isfile(path):
			return False
		
		return True
