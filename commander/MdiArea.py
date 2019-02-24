from deposit import Broadcasts
from deposit.commander.ViewChild import (ViewChild)

from PyQt5 import (QtWidgets, QtCore, QtGui)
from importlib import import_module

class MdiSubWindow(ViewChild, QtWidgets.QMdiSubWindow):

	def __init__(self, model, view, parent):

		self.parent = parent

		ViewChild.__init__(self, model, view)
		QtWidgets.QMdiSubWindow.__init__(self, flags = QtCore.Qt.SubWindow)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		self.windowStateChanged.connect(self.on_state_changed)

	def on_state_changed(self, old_state, new_state):

		self.broadcast(Broadcasts.VIEW_ACTION)

	def closeEvent(self, event):

		self.widget().set_closed()
		self.broadcast(Broadcasts.VIEW_ACTION)

class MdiArea(ViewChild, QtWidgets.QMdiArea):
	
	def __init__(self, model, view):

		self.background_text = "" # [text line, ...]
		self.descriptor_windows = []

		ViewChild.__init__(self, model, view)
		QtWidgets.QMdiArea.__init__(self, view)

		self.set_up()
	
	def set_up(self):
		
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn	)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn	)
		
		self.subWindowActivated.connect(self.on_activated)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
	
	def create(self, frame_name, *args):
		
		window = MdiSubWindow(self.model, self.view, self)
		frame = getattr(import_module("deposit.commander.frames.%s" % (frame_name)), frame_name)(self.model, self.view, window, *args)
		window.setWidget(frame)
		window.setWindowTitle(frame.name())
		window.setWindowIcon(self.view.get_icon(frame.icon()))
		self.addSubWindow(window)
		window.show()
		
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def create_descriptor(self, *args):
		# create Descriptor frame outside of MdiArea
		
		window = getattr(import_module("deposit.commander.frames.Descriptor"), "Descriptor")(self.model, self.view, self.view, *args)
		window.show()
		self.descriptor_windows.append(window)
	
	def close_all(self):
		
		for window in self.descriptor_windows:
			if not window.closed():
				window.hide()
		self.descriptor_windows = []
		self.closeAllSubWindows()
	
	def set_background_text(self, text):
		
		self.background_text = text
		self.hide()
		self.show()
	
	def get_current(self):

		current = self.currentSubWindow()
		if current:
			current = current.widget()
			if hasattr(current, "get_current"):
				return current.get_current()
			return current
		return None
	
	def paintEvent(self, event):

		QtWidgets.QMdiArea.paintEvent(self, event)

		if self.background_text:
			painter = QtGui.QPainter()
			td = QtGui.QTextDocument()
			
			painter.begin(self.viewport())
			painter.translate(QtCore.QPointF(30, 30))
			
			font = td.defaultFont()
			font.setPointSize(10)
			td.setDefaultFont(font)
			td.setHtml(self.background_text)
			td.drawContents(painter)
			
			painter.end()
	
	def on_activated(self):

		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_loaded(self, args):
		
		self.close_all()
	
