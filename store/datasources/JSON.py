from deposit import Broadcasts, __version__
from deposit.store.datasources._FileSource import (FileSource)
from deposit.store.Conversions import (as_url)

from urllib.parse import urlparse
import datetime, time
import shutil
import json
import sys
import os

class JSON(FileSource):
	
	def load_file(self, path):
		
		with open(path, "r") as f:
			data = json.load(f)
		
		# fix for json encoding of integer dict keys
		if "objects" in data:
			data["objects"] = dict([(int(id), data["objects"][id]) for id in data["objects"]])
		
		return data
	
	def save_file(self, data, path):
		
		with open(path, "w") as f:
			json.dump(data, f)
	
