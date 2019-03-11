from deposit import Broadcasts
from deposit.DModule import (DModule)
import time

class Events(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self.stopped = False
		self._events = []  # [[time, user, class_name, key, func_name, args], ...]
		self._last_time = -1
		
		DModule.__init__(self)
		
		self.delements_lookup = dict(
			DObject = self.store.objects,
			DObjects = self.store.objects,
			DClass = self.store.classes,
			DClasses = self.store.classes,
		)
	
	def add(self, element, function, *args):
		
		if self.stopped:
			return
		t = time.time()
		user = None
		if t == self._last_time:
			t = self._last_time + 0.000001
		self._events.append([t, user, element.__class__.__name__, element.key, function.__name__, list(args)])
		self._last_time = t
	
	def clear(self):
		
		self._events = []
		self._last_time = -1
	
	def replicate(self, class_name, key, func_name, args):
		
		if class_name not in self.delements_lookup:
			return
		delement = self.delements_lookup[class_name]
		if key is not None:
			if key not in delement:
				return
			delement = delement[key]
		if not hasattr(delement, func_name):
			return
		return getattr(delement, func_name)(*args)
	
	def stop_recording(self):
		
		self.stopped = True
	
	def resume_recording(self):
		
		self.stopped = False
	
	def to_list(self):
		# returns [[time, user, class_name, key, func_name, args], ...]
		
		return self._events.copy()
	
	def from_list(self, data):
		# data = [[time, user, class_name, key, func_name, args], ...]
		
		self._events = data.copy()

