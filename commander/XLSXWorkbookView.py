from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.XLSXWorkbookModel import XLSXWorkbookModel
from deposit.commander.ExternalHeaderView import ExternalHeaderView
from deposit.commander.ExternalLstView import ExternalLstView
from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
import os

class XLSXWorkbookView(PrototypeList, *uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "XLSXWorkbook.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	def __init__(self, parent_view):
		
		super(XLSXWorkbookView, self).__init__(parent_view)
		self.setupUi(self)
	
	def _populate(self):
		
		for sheet in self._model.sheets():
			model = XLSXWorkbookModel(self._model.parent_model(), self._model.uri(), sheet)
			header_view = ExternalHeaderView(self._parent_view)
			header_view.set_model(model)
			body_view = ExternalLstView(self._parent_view)
			header_view.target_changed.connect(body_view.on_target_changed)
			body_view.set_model(model)
			sheet_view = XLSXSheetView(header_view, body_view)
			self.tabWidget.addTab(sheet_view, sheet)
		
		self.set_title(self._model.filename())
	
	def on_set_model(self):
		
		self._populate()
		

class XLSXSheetView(QtWidgets.QWidget):
	
	def __init__(self, header_view, body_view):
		
		self.headerView = header_view
		self.bodyView = body_view
		
		super(XLSXSheetView, self).__init__()
		
		self.verticalLayout = QtWidgets.QVBoxLayout()
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.verticalLayout.setSpacing(0)
		self.setLayout(self.verticalLayout)
		
		self.verticalLayout.addWidget(self.headerView)
		self.verticalLayout.addWidget(self.bodyView)
		
		self.headerView.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.bodyView.horizontalScrollBar().valueChanged.connect(self.on_horizontalScroll)
		self.headerView.horizontalHeader().sectionResized.connect(self.on_sectionResized)
		
	def on_horizontalScroll(self, position):
		
		self.headerView.horizontalScrollBar().setSliderPosition(position)
		self.bodyView.horizontalScrollBar().setSliderPosition(position)
		
	def on_sectionResized(self, index, oldSize, newSize):
		
		self.bodyView.horizontalHeader().resizeSection(index, newSize)

