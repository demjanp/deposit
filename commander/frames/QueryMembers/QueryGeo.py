from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtWidgets, QtCore, QtGui)

from collections import defaultdict

class QueryGeoLazy(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		self.has_geometry = False
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		def has_geometry():
			
			for row in self.query:
				for column in row:
					descriptor = row[column].descriptor
					if not descriptor is None:
						if descriptor.label.__class__.__name__ == "DGeometry":
							return True
						if (descriptor.label.__class__.__name__ == "DResource") and (not descriptor.label.worldfile is None):
							return True
			return False
		
		self.has_geometry = has_geometry()
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def get_row_count(self):
		
		return int(self.has_geometry)

class GeoModel(DModule):
	
	def __init__(self, model, view, query):
		
		self.model = model
		self.view = view
		self.query = query
		
		self.descriptors = {} # {type: {srid: [DDescriptor, ...], ...}, ...}
		self._row_count = 0

		DModule.__init__(self)
		
		self.set_up()
	
	def set_up(self):
		
		self.descriptors = defaultdict(lambda: defaultdict(list))
		self._row_count = 0
		for row in self.query:
			for column in row:
				descriptor = row[column].descriptor
				typ = None
				srid = -1
				if not descriptor is None:
					if descriptor.label.__class__.__name__ == "DGeometry":
						typ = descriptor.label.type.title()
						srid = descriptor.label.srid
					elif (descriptor.label.__class__.__name__ == "DResource") and (not descriptor.label.worldfile is None):
						typ = "Raster"
						srid = -1 # TODO handle projection for georeferenced rasters
				if not typ is None:
					self.descriptors[typ][srid].append(descriptor)
					self._row_count += 1
	
	def row_count(self):
		
		return self._row_count

class QueryGeo(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		self.geo_model = None
		self.gis_layers = []
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.toolbar = QtWidgets.QToolBar("Geo", self)
		
		# TODO implement toolbar
		for name in ["Act1", "Act2", "Act3"]: # DEBUG
			action = QtWidgets.QAction(name, self)
			action.setData(name)
			self.toolbar.addAction(action)
		
		self.layout.addWidget(self.toolbar)
		
		self.gis_canvas = QtWidgets.QWidget()
		self.layout.addWidget(self.gis_canvas)
		
		self.set_up()
	
	def set_up(self):
		
		self.geo_model = GeoModel(self.model, self.view, self.query)
		self.gis_layers = []

	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def filter(self, text):
		
		pass
	
	def get_selected(self):
		
		return []
	
	def get_row_count(self):
		
		return self.geo_model.row_count()

