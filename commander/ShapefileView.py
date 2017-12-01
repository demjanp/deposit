from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.ExternalHeaderView import ExternalHeaderView
from deposit.commander.ExternalLstView import ExternalLstView
from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
import os

TAB_LST = 0
TAB_GEO = 1

class ShapefileView(PrototypeList, *uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "Shapefile.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	def __init__(self, parent_view):
		
		super(ShapefileView, self).__init__(parent_view)
		self.setupUi(self)
		
		self.headerView = None
		self.lstView = None
		self.geoView = None
	
	def _populate(self):
		
		self.headerView = ExternalHeaderView(self._parent_view)
		self.headerView.set_model(self._model)
		self.verticalLayout.insertWidget(0, self.headerView)
		self.lstView = ExternalLstView(self._parent_view)
		self.headerView.target_changed.connect(self.lstView.on_target_changed)
		self.lstView.set_model(self._model)
		self.tabLst.layout().addWidget(self.lstView)
		self.geoView = ShapefileGeoView(self._parent_view)
		self.geoView.set_model(self._model)
		self.tabGeo.layout().addWidget(self.geoView)
		
		self.headerView.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.lstView.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.headerView.horizontalHeader().sectionResized.connect(self.on_sectionResized)
		
		self.set_title(self._model.filename())
		
	def on_set_model(self):
		
		self._populate()
		
	def on_horizontalScroll(self, position):
		
		self.headerView.horizontalScrollBar().setSliderPosition(position)
		self.lstView.horizontalScrollBar().setSliderPosition(position)
	
	def on_sectionResized(self, index, oldSize, newSize):
		
		self.lstView.horizontalHeader().resizeSection(index, newSize)
		
class ShapefileGeoView(PrototypeList, QtWidgets.QGraphicsView):
	
	def __init__(self, parent_view):
		
		super(ShapefileGeoView, self).__init__(parent_view)
		
	def _populate(self):
		
		pass
	
	def on_set_model(self):
		# TODO
		
		self._populate()
