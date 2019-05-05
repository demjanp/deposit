from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.DescriptorMembers.DescriptorGraphicsView import (DescriptorGraphicsView)
from deposit.commander.frames.DescriptorMembers.ResourceItem import (PixmapItem, SvgItem)

from PySide2 import (QtWidgets, QtCore, QtGui)
import shutil
import os

class Descriptor(Frame, QtWidgets.QMainWindow):
	
	def __init__(self, model, view, parent, descriptor):
		
		self.descriptor = descriptor
		self.actions = {} # {name: QAction, ...}
		self.resource_item = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QMainWindow.__init__(self)
		
		self.set_up()
	
	def name(self):
		
		return str(self.descriptor.label.value)
	
	def icon(self):
		
		return "descriptor.svg"
	
	def set_up(self):
		
		self.central_widget = QtWidgets.QWidget(self)
		self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
		self.central_layout.setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(self.central_widget)
		
		self.statusbar = QtWidgets.QStatusBar(self)
		self.setStatusBar(self.statusbar)
		self.set_up_toolbar()
		
		self.graphics = DescriptorGraphicsView(self.model, self.view, self)
		self.central_layout.addWidget(self.graphics)
		
		self.populate_data()
		
	def set_up_toolbar(self):
		
		self.toolbar = self.addToolBar("Descriptor")
		actions = [
			["object", "Object", "object.svg"],
			["#separator", None, None],
			["zoom_in", "Zoom In", "zoom_in.svg"],
			["zoom_out", "Zoom Out", "zoom_out.svg"],
			["zoom_reset", "Zoom Reset", "zoom_reset.svg"],
			["#separator", None, None],
			["polygon", "Geotag Polygon", "draw_polygon.svg"],
			["remove_geotag", "Remove Geotag", "unlink.svg"],
		]
		
		for name, text, icon in actions:
			if name == "#separator":
				self.toolbar.addSeparator()
			else:
				self.actions[name] = QtWidgets.QAction(self.view.get_icon(icon), text, self)
				self.actions[name].setData(name)
				self.toolbar.addAction(self.actions[name])
		
		self.actions["polygon"].setCheckable(True)
		
		self.actions["polygon"].setEnabled(False) # DEBUG
		self.actions["remove_geotag"].setEnabled(False) # DEBUG
		
		self.toolbar.actionTriggered.connect(self.on_triggered)
	
	def populate_data(self):
		
		if not ((self.descriptor.label.__class__.__name__ == "DResource") and (self.descriptor.label.is_image())):
			return
		
		path = None
		filename = self.model.files.extract_filename(self.descriptor.label.filename)
		f_src = self.descriptor.label.open()
		if not f_src is None:
			path = os.path.join(self.model.files.get_temp_path(), filename)
			f_tgt = open(path, "wb")
			shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
		else:
			return
		
		if os.path.splitext(path)[-1].lower() == ".svg":
			self.resource_item = SvgItem(self, path)
		else:
			self.resource_item = PixmapItem(self, path)
		
		self.graphics.add_item(self.resource_item)
	
	def on_triggered(self, action):
		
		fnc_name = "on_%s" % str(action.data())
		if hasattr(self, fnc_name):
			getattr(self, fnc_name)()
	
	# ToolBox actions:
	
	def on_object(self):
		
		cls = self.descriptor.target.classes
		if cls:
			cls = list(cls.keys())[0]
		else:
			cls = "!*"
		self.view.query("SELECT %s.* WHERE id(%s) == %d" % (cls, cls, self.descriptor.target.id))
	
	def on_polygon(self):
		
		print("draw polygon", self.actions["polygon"].isChecked()) # DEBUG
	
	def on_zoom_in(self):
		
		self.graphics.zoom(1)
	
	def on_zoom_out(self):
		
		self.graphics.zoom(-1)
	
	def on_zoom_reset(self):
		
		self.graphics.zoom()
	
	
	# own events:
	
	def on_activated(self, item):
		
		pass
	
	def on_mouse_enter(self):
		
		pass
		
	def on_mouse_move(self, pos):
		
		pass
		
	def on_mouse_leave(self):
		
		pass
		
	def on_mouse_press(self, pos, button):
		
		pass
		
	def on_mouse_release(self, pos, button):
		
		pass

