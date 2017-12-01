'''
	DC Main Window Model
	--------------------------
	
	Created on 30. 9. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	Public methods:
	

'''
from deposit.commander.ModelActions import ModelActions
from deposit.DB import CHANGED_IDS_EMPTY
from PyQt5 import (QtCore)
from deposit import (Query)
from configparser import ConfigParser
import os
import json
from sys import platform

class MainWindowModel(QtCore.QObject):
	
	store_changed = QtCore.pyqtSignal(dict) # dict = {created: [id, uri, ...], updated: [id, uri, ...], deleted: [id, uri, ...], ordered: [id, uri, ...]}
	
	def __init__(self):
		
		self._view = None
		self.store = None
		self._local_resources = None
		self._check_in_collisions_overwrite = True
		self._srid = None
		self._vertical_srid = None
		self._recent = [] # [[[identifier, connstr], path], ...]; db and file parameters of recently used stores
		self._last_relation = None # label of last Relation used
		self._last_descriptor = None # label of last Descriptor used
		self._last_changed = None
		
		super(MainWindowModel, self).__init__()
		
		self.actions = ModelActions(self)
		self._load_config()
	
	def _save_config(self):
		
		if platform in ["linux", "linux2", "darwin"]:
			cfg_file = os.path.join(os.path.expanduser("~"), "deposit_config.ini")
		else:
			cfg_file = "config.ini"
		
		config = ConfigParser()
		config["Settings"] = {
			"local resources": json.dumps(self._local_resources),
		}
		config["Settings"] = {
			"check in collisions overwrite": json.dumps(self._check_in_collisions_overwrite),
		}
		config["Recent"] = dict([(i, json.dumps(row)) for i, row in enumerate(reversed(self._recent))])
		with open(cfg_file, "w") as f:
			config.write(f)
		f.close()
	
	def _load_config(self):
		
		if platform in ["linux", "linux2", "darwin"]:
			cfg_file = os.path.join(os.path.expanduser("~"), "deposit_config.ini")
		else:
			cfg_file = "config.ini"
		config = ConfigParser()
		config.read(cfg_file)
		if ("Settings" in config) and ("local resources" in config["Settings"]):
			self._local_resources = json.loads(config["Settings"]["local resources"])
		if ("Settings" in config) and ("check in collisions overwrite" in config["Settings"]):
			self._check_in_collisions_overwrite = json.loads(config["Settings"]["check in collisions overwrite"])
		if "Recent" in config:
			for key in sorted(config["Recent"].keys()):
				self._recent.append(json.loads(config["Recent"][key]))
	
	def set_view(self, view):
		
		self._view = view
	
	def set_store(self, store):
		
		self.store_changed.disconnect()
		self._view.close_windows()
		if store == self.store:
			return
		if not store is None:
			params = store.params()
			if not params[0][0] is None: # check if identifier is not None
				if params in self._recent:
					self._recent.remove(params)
				self._recent.append(params)
			self._last_changed = store.get_changed()
		else:
			self._last_changed = None
		self.store = store
		if not self.store is None:
			self.store.set_on_message(self._view.on_store_message)
			self.store.set_on_changed(self.on_store_changed)
			self.store.set_srid(32638, 3855) # DEBUG hardcoded horizontal and vertical SRID
		self._save_config()
		self._view.connect_store_changed()
		self.store_changed.emit(CHANGED_IDS_EMPTY)
	
	def has_store(self):
		
		return not self.store is None
	
	def is_checked_out(self):
		
		return (not self.store is None) and (not self.store.check_out_source() is None)
	
	def id_is_checked_out(self, id):
		
		return (id in self.store.checked_out())
	
	def recent(self):
		
		return self._recent
	
	def clear_recent(self):
		
		self._recent = []
		self._save_config()
		self._view.update_recent()
	
	def query(self, query, relation = None, cls_id = None):
		
		return Query(self.store, query, relation, cls_id)
	
	def last_changed(self):
		
		return self._last_changed
	
	def update_last_changed(self):
		
		if not self.store is None:
			self._last_changed = self.store.get_changed()
		self.store_changed.emit(CHANGED_IDS_EMPTY)
	
	def set_local_resources(self, state):
		
		self._local_resources = state
		self._view.update_action_states()
		self._save_config()
	
	def local_resources(self):
		# return True if resources should be automatically stored locally, False if remotely, None if not specified (always ask)
		
		return self._local_resources
	
	def set_check_in_collisions_overwrite(self, state):
		
		self._check_in_collisions_overwrite = state
		self._view.update_action_states()
		self._save_config()
	
	def check_in_collisions_overwrite(self):
		# return True if colliding Descriptors during check-in should be overwritten in the source database, False if they should be added under a new name
		
		return self._check_in_collisions_overwrite
	
	def srid(self):
		
		return [self._srid, self._vertical_srid]
	
	def set_last_relation(self, label):
		
		self._last_relation = label
	
	def last_relation(self):
		
		return self._last_relation
	
	def set_last_descriptor(self, label):
		
		self._last_descriptor = label
		
	def last_descriptor(self):
		
		return self._last_descriptor
	
	def on_store_changed(self, timestamp, changed_ids):
		
		self.store_changed.emit(changed_ids)

