from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryLst import (QueryLst)
from deposit.commander.frames.QueryMembers.QueryImg import (QueryImgLazy, QueryImg)
from deposit.commander.frames.QueryMembers.QueryGeo import (QueryGeoLazy, QueryGeo)
from deposit.commander.frames.QueryMembers.QueryVis import (QueryVisLazy, QueryVis)
from deposit.commander.frames.QueryMembers.QueryObj import (QueryObj)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Query(Frame, QtWidgets.QWidget):

	def __init__(self, model, view, parent, querystr):

		self.querystr = querystr
		self.query = None
		self.tabs = None
		self.tab_lst = None
		self.tab_img = None
		self.tab_geo = None
		self.tab_vis = None
		self.tab_obj = None
		self.footer = None
		self.populate_obj = [] # [DObject, row] or []
		
		self._update_timer = None
		self._filter_timer = None

		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)

		self.set_up()

	def set_up(self):
		
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.query = self.model.query(self.querystr)
		
		self.tabs = QtWidgets.QTabWidget(self)
		
		self.tab_lst = QueryLst(self.model, self.view, self, self.query)
		self.tabs.addTab(self.tab_lst, "LST")
		
		self.tab_img = QueryImgLazy(self.model, self.view, self, self.query)
		self.tabs.addTab(self.tab_img, "IMG")
		
		self.tab_geo = QueryGeoLazy(self.model, self.view, self, self.query)
		self.tabs.addTab(self.tab_geo, "GEO")
		
		self.tab_vis = QueryVisLazy(self.model, self.view, self, self.query)
		self.tabs.addTab(self.tab_vis, "VIS")
		
		self.tab_obj = QueryObj(self.model, self.view, self, self.query)
		self.tabs.addTab(self.tab_obj, "OBJ")
		
		self.connect_broadcast(Broadcasts.VIEW_SELECTED, self.on_query_selected)
		self.connect_broadcast(Broadcasts.VIEW_BROWSE_PREVIOUS, self.on_previous)
		self.connect_broadcast(Broadcasts.VIEW_BROWSE_NEXT, self.on_next)
		
		self.tabs.currentChanged.connect(self.on_tab_changed)
		
		self.layout.addWidget(self.tabs)
		
		self.footer = QueryFooter(self)
		self.layout.addWidget(self.footer)

		self.footer.set_count(self.tab_lst.get_row_count())
		
		self.update_tabs_enabled()
		
		self.footer.set_zoom_slider(128)
		
		self._update_timer = QtCore.QTimer()
		self._update_timer.setSingleShot(True)
		self._update_timer.timeout.connect(self.on_update_timer)
		self._filter_timer = QtCore.QTimer()
		self._filter_timer.setSingleShot(True)
		self._filter_timer.timeout.connect(self.on_filter_timer)
	
		self.connect_broadcast(Broadcasts.ELEMENT_ADDED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_DELETED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_store_changed)

		self.on_tab_changed(0)

	def update_tabs_enabled(self):

		for i, tab in enumerate([self.tab_img, self.tab_geo, self.tab_vis, self.tab_obj]):
			if tab == self.tab_geo:  # TODO remove after implementing GEO view
				self.tabs.setTabEnabled(i + 1, False)
				continue
			self.tabs.setTabEnabled(i + 1, (tab.get_row_count() > 0))
	
	def populate_tab_img(self):
		
		self.tab_img = QueryImg(self.model, self.view, self, self.query)
		self.connect_broadcast(Broadcasts.VIEW_SELECTED, self.on_query_selected)
		self.tab_img.set_thumbnail_size(128)
		
		self.tabs.insertTab(1, self.tab_img, "IMG")
		self.tabs.removeTab(2)
		self.tabs.setCurrentIndex(1)
		
		self.on_sorted()
	
	def populate_tab_geo(self):
		
		self.tab_geo = QueryGeo(self.model, self.view, self, self.query)
		self.connect_broadcast(Broadcasts.VIEW_SELECTED, self.on_query_selected)
		
		self.tabs.insertTab(2, self.tab_geo, "GEO")
		self.tabs.removeTab(3)
		self.tabs.setCurrentIndex(2)
	
	def populate_tab_vis(self):
		
		self.tab_vis = QueryVis(self.model, self.view, self, self.query)
		self.connect_broadcast(Broadcasts.VIEW_SELECTED, self.on_query_selected)
		
		self.tabs.insertTab(3, self.tab_vis, "VIS")
		self.tabs.removeTab(4)
		self.tabs.setCurrentIndex(3)
	
	def update(self):
		
		query = self.model.query(self.querystr)

		if not((len(self.query.hash) == len(query.hash)) and (self.query.hash == query.hash)):
			self.query = query
			self.tab_lst.set_query(self.query)
			self.tab_img.set_query(self.query)
			self.tab_geo.set_query(self.query)
			self.update_tabs_enabled()
		
		self.tab_vis.set_query(self.query)
		
		self.tab_obj.set_query(self.query)
		if self.tab_obj.object is not None:
			self.tab_obj.update()

		self.on_filter_timer()
		self.on_sorted()

	def name(self):

		return self.querystr
	
	def get_mime_data(self, indexes):
		
		return self.tab_lst.table_model.mimeData(indexes)
	
	def get_current(self):

		return [self.tab_lst, self.tab_img, self.tab_geo, self.tab_vis, self.tab_obj][self.tabs.currentIndex()]

	def on_query_selected(self, args):

		if self.closed():
			return

		broadcaster = args[0][0]
		if (broadcaster.__class__.__name__ != "QueryLst") or (broadcaster.relation is not None):
			return
		
		obj, row = self.tab_lst.get_first_selected()
		if obj is None:
			return
		if self.tabs.currentIndex() == 4:  # obj tab visible
			self.tab_obj.populate_data(self.tab_lst, obj, row)
			self.populate_obj = []
		else:
			self.populate_obj = [obj, row]
	
	@QtCore.Slot(int)
	def on_tab_changed(self, index):
		
		if index == 4: # tab_obj
			if not self.tab_lst.get_selected_objects():
				self.tab_lst.select_next_row()
			if self.populate_obj:
				self.tab_obj.populate_data(self.tab_lst, *self.populate_obj)
		
		elif index == 1: # tab_img
			if isinstance(self.tab_img, QueryImgLazy):
				self.populate_tab_img()
		
		elif index == 2: # tab_geo
			if isinstance(self.tab_geo, QueryGeoLazy):
				self.populate_tab_geo()
		
		elif index == 3: # tab_vis
			if isinstance(self.tab_vis, QueryVisLazy):
				self.populate_tab_vis()
		
		self.footer.set_zoom_enabled(index == 1)
		self.footer.set_filter_enabled(index != 4)

		if index != 4:
			self.on_filter_timer()
		
		self.footer.set_count(self.get_current().get_row_count())

		state = ((index in [0,4]) and (len(self.query.parse.selects) == 1) and (len(self.query.parse.selects[0].classes) == 1))
		self.footer.set_add_object_enabled(state)

		self.update_tabs_enabled()
		self.on_sorted()
	
	def on_filter(self):
		
		self._filter_timer.start(1000)
	
	def on_filter_timer(self):
		
		self.get_current().filter(self.footer.filter_edit.text())
		self.footer.set_count(self.get_current().get_row_count())
	
	def on_sorted(self):
		
		if isinstance(self.tab_img, QueryImgLazy):
			return
		row_ids = self.tab_lst.get_row_ids()  # {object id: row, ...}
		self.tab_img.set_row_ids(row_ids)
	
	def on_zoom(self, value):

		current = self.get_current()
		if current == self.tab_img:
			current.set_thumbnail_size(value)
	
	def on_previous(self, args):

		for broadcaster, in args:
			if broadcaster == self.tab_obj.browse_frame:
				self.tab_lst.select_previous_row()
	
	def on_next(self, args):

		for broadcaster, in args:
			if broadcaster == self.tab_obj.browse_frame:
				self.tab_lst.select_next_row()
	
	def on_add_object(self):

		cls = self.query.classes[0]
		if cls == "!*":
			self.model.objects.add()
		else:
			self.model.classes[cls].objects.add()
		if self.get_current() == self.tab_obj:
			self.update()
			self.tab_lst.select_last_row()
	
	def on_store_changed(self, args):
		
		self._update_timer.start(100)
	
	@QtCore.Slot()
	def on_update_timer(self):
		
		if not self.edited:
			self.update()
		else:
			self.edited = False
	
	def on_object_activated(self, element):
		
		self.tabs.setCurrentIndex(4)
	
	def on_descriptor_activated(self, element):
		
		if element.label.__class__.__name__ == "DResource":
			if element.label.is_image():
				self.view.mdiarea.create_descriptor(element)
				return
			self.model.files.open(element.label)
	
	def on_query_activated(self, querystr):
		
		self.view.query(querystr)
	
class QueryFooter(DModule, QtWidgets.QFrame):

	def __init__(self, queryframe):

		self.queryframe = queryframe
		self.count_text = None

		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self)

		self.set_up()

	def set_up(self):

		self.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.setFrameShadow(QtWidgets.QFrame.Raised)

		self.layout = QtWidgets.QGridLayout()
		self.layout.setContentsMargins(5, 0, 0, 0)
		self.layout.setSpacing(10)
		self.setLayout(self.layout)

		self.add_object_button = QtWidgets.QToolButton()
		self.add_object_button.setIcon(self.queryframe.view.get_icon("add_object.svg"))
		self.add_object_button.setIconSize(QtCore.QSize(24, 24))
		self.add_object_button.setAutoRaise(True)
		self.add_object_button.setToolTip("Add Object")
		self.add_object_button.clicked.connect(self.queryframe.on_add_object)
		self.layout.addWidget(self.add_object_button, 0, 0)

		self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.zoom_slider.setMinimum(64)
		self.zoom_slider.setMaximum(256)
		self.zoom_slider.valueChanged.connect(self.queryframe.on_zoom)
		self.set_zoom_enabled(False)
		self.layout.addWidget(self.zoom_slider, 0, 1)

		filter_label = QtWidgets.QLabel("Filter:")
		self.layout.addWidget(filter_label, 0, 2)

		self.filter_edit = QtWidgets.QLineEdit()
		self.filter_edit.textEdited.connect(self.queryframe.on_filter)
		self.layout.addWidget(self.filter_edit, 0, 3)

		self.count_label = QtWidgets.QLabel("Found: %s")
		self.count_label.setContentsMargins(0, 0, 3, 0)
		self.layout.addWidget(self.count_label, 0, 4)

		self.count_text = self.count_label.text()

	def set_zoom_slider(self, value):

		self.blockSignals(True)
		self.zoom_slider.setValue(value)
		self.blockSignals(False)

	def set_count(self, count):

		self.count_label.setText(self.count_text % (count))

	def set_zoom_enabled(self, state):

		self.zoom_slider.setEnabled(state)
		self.zoom_slider.setVisible(state)

	def set_filter_enabled(self, state):

		self.filter_edit.setEnabled(state)

	def set_add_object_enabled(self, state):

		self.add_object_button.setVisible(state)
