from deposit.DModule import (DModule)

from functools import wraps

class DElement(DModule):
	
	def __init__(self, parent):
		
		self.parent = parent
		
		super(DElement, self).__init__()
		
		self.store = self.parent
		while isinstance(self.store, DElement) or isinstance(self.store, DElements):
			self.store = self.store.parent
	
	@property
	def key(self):
		
		return None
	
	def to_dict(self):
		
		return dict(
			delement = self.__class__.__name__,
		)
	
	def from_dict(self, data):
		
		pass

class DElements(DModule):
	
	def __init__(self, parent):
		
		self.parent = parent # a Store or DElement object
		self._members = {} # {key: DElement instance, ...}
		self._keys = [] # [key, ...]
		self._pos = 0
		
		super(DElements, self).__init__()
		
		self.store = self.parent
		while isinstance(self.store, DElement) or isinstance(self.store, DElements):
			self.store = self.store.parent
	
	@property
	def key(self):
		
		return None
	
	def get_new_id(self, main_elements):
		# generate new id unique to main_elements
		
		ids = sorted(main_elements.keys())
		if not ids:
			return 0
		if (ids[0] == 0) and (ids[-1] == len(ids) - 1):
			return len(ids)
		for id in range(len(ids)):
			if ids[id] != id:
				return id
		return len(ids)
	
	def keys(self):
		
		return self._keys.copy()
	
	def __len__(self):
		
		return len(self._keys)
	
	def __contains__(self, key):
		
		return key in self._keys
	
	def __getitem__(self, key):
		
		if key in self._members:
			return self._members[key]
		raise IndexError()
	
	def add_naive(self, key, member):
		
		self._members[key] = member
		self._keys.append(key)
	
	def __setitem__(self, key, member):
		
		self._members[key] = member
		if not key in self._keys:
			self._keys.append(key)
	
	def __iter__(self):
		
		for key in self._keys:
			yield key
	
	def __next__(self):
		
		if self._pos < len(self._keys):
			self._pos += 1
			return self._keys[self._pos - 1]
		else:
			self._pos = 0
			raise StopIteration()
	
	def del_naive(self, key):
		
		if key in self._members:
			del self._members[key]
			self._keys.remove(key)
	
	def __delitem__(self, key):
		
		if key in self._members:
			self.del_naive(key)
	
	def switch_order(self, key1, key2):
		
		if not ((key1 in self._keys) and (key2 in self._keys)):
			return False
		i1 = self._keys.index(key1)
		i2 = self._keys.index(key2)
		self._keys[i1], self._keys[i2] = self._keys[i2], self._keys[i1]
		return True
	
	def to_dict(self):
		
		return dict([(key, self._members[key] if isinstance(self._members[key], dict) else self._members[key].to_dict()) for key in self._keys])
	
	def from_dict(self, data):
		
		pass

def event(function):
	# event decorator for DElement and DElements
	
	@wraps(function)
	def wrapper(self, *args):
		
		self.store.events.add(self, function, *args)
		
		return function(self, *args)
	
	return wrapper

