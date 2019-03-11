from deposit import Broadcasts
from deposit.store.datasources._DataSource import (DataSource)

from urllib.parse import urlparse
import datetime, time
import shutil
import json
import os

class JSON(DataSource):

	def __init__(self, store, url = None):

		DataSource.__init__(self, store)
		
		self.set_url(url)
	
	def set_url(self, url):
		
		if url is None:
			self.url = None
			self.identifier = None
		else:
			self.url = url
			self.identifier = os.path.splitext(url)[0] + "#"
		if self.store.data_source == self:
			self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)

	def load(self):
		
		if self.url is None:
			return False
		
		self.stop_broadcasts()
		self.store.events.stop_recording()
		self.store.clear()
		
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//")))
		
		data = None
		with open(path, "r") as f:
			data = json.load(f)
		
		# fix for json encoding of integer dict keys
		data["objects"] = dict([(int(id), data["objects"][id]) for id in data["objects"]])
		
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
		self.store.local_folder = data["local_folder"]
		
		if "events" in data: # TODO will be obsolete for new databases
			self.store.events.from_list(data["events"])
		
		self.store.images.load_thumbnails()
		
		self.store.set_datasource(self)
		
		self.store.events.resume_recording()
		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)

		return True

	def save(self):

		if self.url is None:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
			return False
		
		data = dict(
			classes = self.store.classes.to_dict(), # {name: class data, ...}
			objects = self.store.objects.to_dict(), # {id: object data, ...}
			changed = self.store.changed,
			local_folder = self.store.local_folder,
			events = self.store.events.to_list() if self.store.save_events else [],
		)
		
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//")))
		
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
		
		with open(path, "w") as f:
			json.dump(data, f)
		
		self.broadcast(Broadcasts.STORE_SAVED)
		return True
