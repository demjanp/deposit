from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.QueryLstView import QueryLstView
from deposit.commander.QueryImgView import QueryImgView
from deposit.commander.QueryGeoView import QueryGeoView
from deposit.commander.QueryObjView import QueryObjView
from deposit.commander.RelationsView import RelationsView
from deposit.commander.ClassesFrame import ClassesFrame
from deposit.commander.ObjectFrame import ObjectFrame
from deposit.DLabel import (id_to_name)
from PyQt5 import (uic, QtWidgets, QtCore)
import os

TAB_LST = 0
TAB_IMG = 1
TAB_GEO = 2
TAB_OBJ = 3

class QueryView(PrototypeList, *uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "Query.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	def __init__(self, parent_view, object_first):
		
		self._object_first = object_first
		self._browse_row = 0
		self._count_text = "%d"
		self._relation_data = []
		self._object_added = False
		
		super(QueryView, self).__init__(parent_view)
		self.setupUi(self)
		
		self.lstView = None
		self.imgView = None
		self.geoView = None
		self.objView = None
		self.relations = None
		
		self.orderUpButton.clicked.connect(self.on_order_up)
		self.orderDownButton.clicked.connect(self.on_order_down)
		
	def _set_up_object_and_classes_frame(self):
		
		self.object_frame = ObjectFrame(self)
		self.object_frame.setParent(self)
		self.classes_frame = ClassesFrame(self)
		self.classes_frame.setParent(self)
		self.classes_frame.set_model(self._model)
		self._model.store_changed.connect(self.classes_frame.on_store_changed)
		self.object_classes_frame = QtWidgets.QFrame()
		oc_layout = QtWidgets.QHBoxLayout()
		self.object_classes_frame.setLayout(oc_layout)
		oc_layout.setContentsMargins(1, 0, 0, 3)
		oc_layout.addWidget(self.object_frame)
		oc_layout.addWidget(self.classes_frame)
		oc_layout.addStretch()
		self.browseFrame.layout().insertWidget(0, self.object_classes_frame)
	
	def _browse_to_obj(self, row):
		
		self.set_obj_row(self.lstView.item(row, 0).data(QtCore.Qt.UserRole)["data"]["row"])
	
	def _update_relation_data(self):
		
		self._relation_data = self._model.object_relations()
	
	def _update_order_enabled(self):
		
		if self.tabWidget.currentIndex() == TAB_LST:
			item = self.lstView.currentItem()
			if item:
				data = item.data(QtCore.Qt.UserRole)
				if data and ("column" in data["data"]):
					column = data["data"]["column"]
					self.orderUpButton.setEnabled(column > 0)
					self.orderDownButton.setEnabled(column < self.lstView.columnCount() - 2)
					return
		self.orderUpButton.setEnabled(False)
		self.orderDownButton.setEnabled(False)
	
	def _populate(self):
		
		self.lstView = QueryLstView(self)
		self.lstView.setParent(self)
		self.lstView.set_model(self._model)
		self._model.store_changed.connect(self.lstView.on_store_changed)
		
		self._count_text = self.countLabel.text()
		
		self.newButton.setEnabled(not self._model.parent_class() is None)
		
		if self._model.has_relation():
			self.tabWidget.hide()
			self.footerFrame.hide()
			self.layout().addWidget(self.lstView)
		
		else:
			self.set_title(self._model.query_str())
			
			self.tabLst.layout().addWidget(self.lstView)
			self.footerFrame.show()
			
			self.imgView = QueryImgView(self)
			self.imgView.setParent(self)
			self.imgView.set_model(self._model)
			self._model.store_changed.connect(self.imgView.on_store_changed)
			self.imgView.set_thumb_size(128)
			self.set_zoom_slider(self.imgView.thumb_size())
			self.tabImg.layout().addWidget(self.imgView)
			
			self.geoView = QueryGeoView(self)
			self.geoView.setParent(self)
			self.geoView.set_model(self._model)
			self._model.store_changed.connect(self.geoView.on_store_changed)
			self.tabGeo.layout().addWidget(self.geoView)
			
			self.objView = QueryObjView(self)
			self.objView.setParent(self)
			self.objView.set_model(self._model)
			self._model.store_changed.connect(self.objView.on_store_changed)
			self.objectLayout.addWidget(self.objView)
			
			self._set_up_object_and_classes_frame()
			
			self.relations = RelationsView()
			self.relationsLayout.addWidget(self.relations)
			self._update_relation_data()
			
			self.update_tabs_enabled()
		
		if self._object_first:
			self.set_obj_row(0)
		self._update_order_enabled()

	def _populate_relations(self, row):
		
		if not "obj_id" in self._model.object_data(row)["data"]:
			return
		obj_id = self._model.object_data(row)["data"]["obj_id"]
		items = [] # [[widget, label], ...]
		for rel, cls, cls_id, rev in self._relation_data:
			query = "%(cls)s.%(rel)s.obj(%(id)s) and (%(cls)s.* or %(cls)s)" % {"cls": cls, "rel": rel if rev else ("~" + rel), "id": id_to_name(obj_id)}
			items.append([self._parent_view.get_query(query, relation = [obj_id, rel, cls, cls_id, not rev], cls_id = cls_id), ". %s . %s" % (("~" + rel) if rev else rel, cls)])
		self.relations.set_items(items)
	
	def _current_widget(self):
		
		idx = self.tabWidget.currentIndex()
		if idx == TAB_LST:
			return self.lstView
		elif idx == TAB_IMG:
			return self.imgView
		elif idx == TAB_GEO:
			return self.geoView
		elif idx == TAB_OBJ:
			return self.objView
	
	def update_tabs_enabled(self):
		
		self.tabWidget.setTabEnabled(TAB_IMG, self._model.has_images())
		self.tabWidget.setTabEnabled(TAB_GEO, self._model.has_geometry())
	
	def set_obj_row(self, row):
		
		if (row < 0) or (row > self._model.row_count() - 1):
			return
		obj_id = self._model.objects()[row]
		self.objView.set_row(row)
		self.object_frame.set_object(obj_id)
		self.classes_frame.set_object(obj_id)
		self._populate_relations(row)
	
	def set_zoom_slider(self, value):
		
		self.blockSignals(True)
		self.zoomSlider.setValue(value)
		self.blockSignals(False)
	
	def set_count(self, value):
		
		self.countLabel.setText(self._count_text % value)
	
	def on_set_model(self):
		
		self._populate()
		if self._object_first:
			self.tabWidget.setCurrentIndex(TAB_OBJ)
		self.zoomSlider.setVisible(self.tabWidget.currentIndex() == TAB_IMG)
		self.tabWidget.currentChanged.connect(self.on_tab_changed)
		self.filterEdit.textEdited.connect(self.on_filter)
		self.zoomSlider.valueChanged.connect(self.on_zoom)
	
	def on_store_changed(self, ids):
		# called by main view
		
		self._update_relation_data()
		self.update_tabs_enabled()
		if self._object_added:
			self.set_obj_row(self._model.objects().index(self._object_added))
		else:
			if ids and (not self.objView is None) and ((self.objView.obj_id() in ids["updated"]) or (self.objView.obj_id() in ids["deleted"])):
				self._populate_relations(self.objView.row())
		self._object_added = False
	
	def on_selection_changed(self):
		
		self._update_order_enabled()
		super(QueryView, self).on_selection_changed()
	
	def on_activated(self, item):
		
		data = item.data(QtCore.Qt.UserRole)
		if data["parent"] == "QueryModel":
			if "rel_id" in data["data"]: # open Descriptor
				if data["data"]["geometry"] or data["data"]["image"] or data["data"]["obj3d"]:
					self._parent_view.open_descriptor(data["data"]["obj_id"], data["data"]["rel_id"]) # id_rel is an Image, Geometry or 3D Descriptor
				elif data["data"]["storage_type"]: # id_rel is another Resource
					self._parent_view.open_resource(data["data"]["obj_id"], data["data"]["rel_id"])
				else: # open Object in separate window
					self._parent_view.open_object(data["data"]["obj_id"])
			else:
				if self._model.has_relation(): # open Object in separate window
					self._parent_view.open_object(data["data"]["obj_id"])
				else: # open Object in OBJ tab
					self.set_obj_row(data["data"]["row"])
					self._browse_row = item.row()
					self.tabWidget.setCurrentIndex(TAB_OBJ)
		elif data["parent"] == "ObjectFrame":
			self._parent_view.open_object(data["data"]["obj_id"])
		elif data["parent"] == "ClassesFrame":
			self._parent_view.open_class(data["data"]["cls_id"])
	
	def on_tab_changed(self, idx):
		
		self.footerFrame.setVisible(idx != TAB_OBJ)
		self.zoomSlider.setVisible(idx == TAB_IMG)
		if (idx == TAB_OBJ) and (self.objView.row() is None):
			data = self.lstView.selected()
			if data:
				self.set_obj_row(int(data[0]["data"]["row"]))
			else:
				self.set_obj_row(0)
		self._update_order_enabled()
		self.on_filter()
	
	def on_count_changed(self, count):
		
		self.set_count(count)
	
	def on_order_up(self, *args):
		# TODO change selection
		
		current = self.lstView.selected()[0]["data"]
		prev = self.lstView.item(current["row"], current["column"]).data(QtCore.Qt.UserRole)["data"]
		to_swap = [current["cls_id"], prev["cls_id"]]
		self._model._parent_model.store.swap_order(*to_swap)
		# TODO change selection
#		self.lstView.setCurrentCell(prev["row"], prev["column"] + 1)
		
	def on_order_down(self, *args):
		# TODO change selection
		
		current = self.lstView.selected()[0]["data"]
		next = self.lstView.item(current["row"], current["column"] + 2).data(QtCore.Qt.UserRole)["data"]
		to_swap = [current["cls_id"], next["cls_id"]]
		self._model._parent_model.store.swap_order(*to_swap)
		# TODO change selection
#		self.lstView.setCurrentCell(next["row"], next["column"] + 1)
		
	@QtCore.pyqtSlot()
	def on_prevButton_clicked(self):
		
		if self._browse_row > 0:
			self._browse_row -= 1
			self._browse_to_obj(self._browse_row)
	
	@QtCore.pyqtSlot()
	def on_nextButton_clicked(self):
		
		if self._browse_row < self.lstView.rowCount() - 1:
			self._browse_row += 1
			self._browse_to_obj(self._browse_row)
	
	@QtCore.pyqtSlot()
	def on_newButton_clicked(self):
		
		cls_id = self._model.parent_class()
		if cls_id:
			self._object_added = self._model._parent_model.store.objects.add()
			self._model._parent_model.store.members.add(cls_id, self._object_added)
	
	def on_filter(self, text = None):
		
		if text is None:
			text = self.filterEdit.text()
		
		widget = self._current_widget()
		if widget:
			widget.on_filter(text)
	
	def on_zoom(self, value):
		
		widget = self._current_widget()
		if widget:
			widget.on_zoom(value)
	
	def sizeHint(self):
		
		size = super(QueryView, self).sizeHint()
		max_w, max_h = size.width(), size.height()
		if self.relations:
			min_h = min(12, size.height())
			for item in self.relations.items():
				min_h += min(12, item.sizeHint().height())
			max_h = max(max_h, min_h)
		size.setWidth(min(size.width(), max_w))
		size.setHeight(min(size.height(), max_h))
		return size
