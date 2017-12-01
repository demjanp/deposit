import json

class PrototypeFrame(object):
	
	def __init__(self, parent_view):
		
		self._parent_view = parent_view
		super(PrototypeFrame, self).__init__()
	
	def _eval_drag(self, event):
		
		source = None
		data = event.mimeData()
		if "application/deposit" in data.formats():
			source = json.loads(data.data("application/deposit").data().decode("utf-8"))
		elif data.hasUrls():
			source = dict(parent = "external", data = [dict(value = url.toString()) for url in data.urls()])
		if not source is None:
			data = [{}]
			if hasattr(self, "get_data"):
				data = [self.get_data()]
			target = dict(parent = self.__class__.__name__, data = data, paths = [])
			for src_data in source["data"]:
				if not self.get_drop_action(source["parent"], src_data, target["data"][0]) is None:
					if hasattr(event, "accept"):
						event.accept()
					return source, target
		event.ignore()
		return None, None
	
	def get_drop_action(self, src_parent, src_data, tgt_data):
		# re-implement to enable drag & drop
		# src_parent = name of parent class
		# src_data / tgt_data = dict(
		#	obj_id = obj_id,
		#	row = row,
		#	column = column,
		#	cls_id = cls_id,
		#	rel_id = rel_id,
		#	value = value,
		#	read_only = True/False,
		#	image = True/False
		#	geometry = True/False
		#	obj_id2 = obj_id (related),
		#	rel_label = label,
		#	reversed = True/False,
		#	parent_class = cls_id,
		#	coords = [[x, y], ...],
		#	path = path,
		#	filename = filename,
		#	thumbnail = thumbnail,
		# )
		# return DragAction
		
		return None
	
	def process_drop(self, *args):
		
		self._parent_view.process_drop(*args)
	
	def on_store_changed(self, ids):
		
		pass
	
	def on_drag_leave(self, event):
		
		pass
	
	def on_drag_move(self, source, target, event):
		
		pass
	
	def on_drop(self, event):
		
		pass
	
	def dragEnterEvent(self, event):
		
		event.accept()
	
	def dragLeaveEvent(self, event):
		
		self.on_drag_leave(event)
	
	def dragMoveEvent(self, event):
		
		source, target = self._eval_drag(event)
		if not source is None:
			self.on_drag_move(source, target, event)
	
	def dropEvent(self, event):
		
		source, target = self._eval_drag(event)
		if not source is None:
			self._parent_view.process_drop(self, source["parent"], source["data"], target["data"][0], event)
		self.on_drop(event)
	
	