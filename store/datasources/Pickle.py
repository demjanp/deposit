from deposit import Broadcasts, __version__
from deposit.store.datasources._FileSource import (FileSource)
from deposit.store.Conversions import (as_url)

from urllib.parse import urlparse
import datetime, time
import shutil
import pickle
import sys
import os

class Pickle(FileSource):
	
	def load_file(self, path):
		
		with open(path, "rb") as f:
			data = pickle.load(f)
		
		return data
	
	def save_file(self, data, path):
		
		with open(path, "wb") as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
			
