
from collections import defaultdict

VIEW_ACTION = 0
VIEW_SELECTED = 1
VIEW_BROWSE_PREVIOUS = 2
VIEW_BROWSE_NEXT = 3
VIEW_OBJECT_ACTIVATED = 4
VIEW_DESCRIPTOR_ACTIVATED = 5

STORE_SAVED = 100
STORE_SAVE_FAILED = 101
STORE_LOADED = 102
STORE_LOCAL_FOLDER_CHANGED = 103
STORE_DATA_SOURCE_CHANGED = 104
STORE_DATA_CHANGED = 105

ELEMENT_ADDED = 200
ELEMENT_CHANGED = 201
ELEMENT_DELETED = 202

MAX_BROADCASTS_PER_SIGNAL = 100

class BroadcastHook(object):

	def __init__(self):

		self._connected = defaultdict(list)  # {signal: [func, dmodule, args], ...}
		self._broadcasts = defaultdict(list)  # {signal: [broadcaster, args], ...}
		self._stopped = False
		self._on_broadcast = None

	def set_on_broadcast(self, func):

		self._on_broadcast = func

	def add(self, broadcaster, signal, args):

		if self._stopped:
			return
		if signal in self._connected:
			if len(self._broadcasts[signal]) >= MAX_BROADCASTS_PER_SIGNAL:
				return
			if [broadcaster, args] not in self._broadcasts[signal]:
				self._broadcasts[signal].append([broadcaster, args])
				if self._on_broadcast is not None:
					self._on_broadcast()

	def connect(self, dmodule, signal, func, args):
		# args: list of additional arguments passed to function

		if [func, dmodule, args] not in self._connected[signal]:
			self._connected[signal].append([func, dmodule, args])

	def disconnect(self, dmodule, signal = None):

		if signal is None:
			signals = list(self._connected.keys())
		elif signal in self._connected:
			signals = [signal]
		else:
			return

		for signal in signals:
			to_del = [idx for idx in range(len(self._connected[signal])) if self._connected[signal][idx][1] == dmodule]
			if len(to_del) == len(self._connected[signal]):
				del self._connected[signal]
			else:
				for idx in reversed(to_del):
					del self._connected[signal][idx]

	def broadcast(self):

		if self._stopped:
			return
		to_exec = []
		for signal in list(self._broadcasts.keys()):
			if self._broadcasts[signal] and (signal in self._connected):
				for func, _, args2 in self._connected[signal]:
					args = []
					for broadcaster, args1 in self._broadcasts[signal]:
						args.append([broadcaster] + args1 + args2)

					to_exec.append([func, args])
		self._broadcasts.clear()

		for func, args in to_exec:
			func(args)

	def stop(self):

		self._stopped = True

	def resume(self):

		if self._stopped:
			self._stopped = False
			if self._on_broadcast is None:
				self.broadcast()
			else:
				self._on_broadcast()

_BROADCAST_HOOK = BroadcastHook()
