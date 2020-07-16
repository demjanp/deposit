from deposit import Broadcasts
from PySide2 import (QtWidgets)

def check_visible(function):
	
	def wrapper(self, *args):
		
		if isinstance(self, QtWidgets.QWidget):
			if not self.isVisible():
				return
		return function(self, *args)
	
	return wrapper

class DModule(object):
	
	@check_visible
	def broadcast(self, signal, *args):
		
		Broadcasts._BROADCAST_HOOK.add(self, signal, list(args))

	def connect_broadcast(self, signal, func, *args):
		# *args: additional arguments passed to function
		# func gets called as func(args); args = [[broadcaster DModule, arg1, arg2, ...], ...]

		Broadcasts._BROADCAST_HOOK.connect(self, signal, func, list(args))

	def disconnect_broadcast(self, signal = None):

		Broadcasts._BROADCAST_HOOK.disconnect(self, signal)

	def stop_broadcasts(self):

		Broadcasts._BROADCAST_HOOK.stop(id(self))

	def resume_broadcasts(self):

		Broadcasts._BROADCAST_HOOK.resume(id(self))
	
	@check_visible
	def process_broadcasts(self):

		Broadcasts._BROADCAST_HOOK.broadcast()

	def set_on_broadcast(self, func):

		Broadcasts._BROADCAST_HOOK.set_on_broadcast(func)

