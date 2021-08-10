from deposit import Broadcasts
from deposit.commander.ViewChild import (ViewChild)

from deposit.commander.frames import FRAMES

from PySide2 import (QtWidgets, QtCore, QtGui)
from collections import defaultdict
import json

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
		QtWidgets.QMdiArea.__init__(self, view.navigator)

		self.set_up()
	
	def set_up(self):
		
		self.setAcceptDrops(True)
		
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		
		self.subWindowActivated.connect(self.on_activated)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
	
	def create(self, frame_name, *args):
		
		if frame_name not in FRAMES:
			return
		window = MdiSubWindow(self.model, self.view, self)
		frame = FRAMES[frame_name](self.model, self.view, window, *args)
		window.setWidget(frame)
		window.setWindowTitle(frame.name())
		window.setWindowIcon(self.view.get_icon(frame.icon()))
		self.addSubWindow(window)
		window.show()
		
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def create_descriptor(self, *args):
		# create Descriptor frame outside of MdiArea
		
		window = FRAMES["Descriptor"](self.model, self.view, self.view, *args)
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
	
	def open_external(self, url):
		
		ext = url.split(".")[-1].lower()
		es = None
		if ext == "xlsx":
			es = self.model.externalsources.XLSX(url)
		elif ext == "csv":
			es = self.model.externalsources.CSV(url)
		elif ext == "shp":
			es = self.model.externalsources.Shapefile(url)
		if (es is not None) and es.load():
			self.create(es.name, es)
	
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
	
	def get_drag_data(self, event):
		
		mimedata = event.mimeData()
		if "application/deposit" in mimedata.formats():
			rows = mimedata.data("application/deposit")
			rows = rows.data().decode("utf-8").strip()
			if not rows:
				cb = QtWidgets.QApplication.clipboard()
				mimedata = cb.mimeData()
				if "application/deposit" in mimedata.formats():
					rows = mimedata.data("application/deposit")
					rows = rows.data().decode("utf-8").strip()
			if rows:
				rows = json.loads(rows)
				objects = []
				for row in rows:
					id = None
					if row["delement"] == "DObject":
						id, identifier, connstr = int(row["id"]), row["identifier"], row["connstr"]
					elif row["delement"] == "DDescriptor":
						id, identifier, connstr = int(row["target"]), row["identifier"], row["connstr"]
					if (id is not None):
						if (identifier != self.model.identifier) or (connstr != self.model.connstr):
							objects.append([id, identifier, connstr])					
				if objects:
					return "objects", objects
				elif len(rows):
					return "objects", None
		if mimedata.hasUrls():
			for url in mimedata.urls():
				url = str(url.toString())
				if url.split(".")[-1].lower() in ["pickle", "json", "xlsx", "csv", "shp"]:
					return "url", url
		return None, None
	
	def dragEnterEvent(self, event):
		
		typ, data = self.get_drag_data(event)
		if typ is None:
			event.ignore()
			return
		event.accept()
	
	def dragMoveEvent(self, event):
		
		typ, data = self.get_drag_data(event)
		if typ is None:
			event.ignore()
			return
		event.accept()
	
	def dropEvent(self, event):
		
		typ, data = self.get_drag_data(event)
		if typ == "url":
			ext = data.split(".")[-1].lower()
			if ext in ["json", "pickle"]:
				url = "%s" % (data)
				self.view.dialogs.open("OpenOrImport", url)
				return
			self.open_external(data)
			return
		
		if typ == "objects":
			if data is None:
				QtWidgets.QMessageBox.warning(self, "Import Error", "Cannot import from an unsaved database.")
			else:
				groups = defaultdict(lambda: defaultdict(list)) # {identifier: {connstr: [id, ...], ...}, ...}
				for id, identifier, connstr in data:
					groups[identifier][connstr].append(id)
				for identifier in groups:
					for connstr in groups[identifier]:
						self.model.add_objects(identifier, connstr, groups[identifier][connstr], localise = True)
	
	def on_activated(self):

		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_loaded(self, args):
		
		self.close_all()
	
