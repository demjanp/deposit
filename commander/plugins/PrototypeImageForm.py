from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.plugins.PrototypePlugin import PrototypePlugin
from deposit.commander.plugins.PrototypeForm import PrototypeForm
from deposit.commander.DropActions import DropActions
from deposit.commander.MainWindowView import signal_handler
from deposit.store.Resources import Resources
from deposit.DLabel import (DString)
from PyQt5 import (uic, QtWidgets, QtCore, QtGui)

class ImageList(PrototypeList, QtWidgets.QListWidget):
	
	def __init__(self, parent_view):
		
		super(ImageList, self).__init__(parent_view)
		
		self._obj_id = None
		self._cls_id = None
		
		self.setMinimumWidth(290)
		self.setIconSize(QtCore.QSize(256, 256))
		self.setWrapping(True)
		self.setResizeMode(QtWidgets.QListView.Adjust)
		self.setViewMode(QtWidgets.QListView.IconMode)
		self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		
		self.set_drag_and_drop_enabled()
		
	def obj_id(self):
		
		return self._obj_id
	
	def cls_id(self):
		
		return self._cls_id
	
	def set_obj_cls(self, obj_id, cls_id):
		
		self._obj_id = obj_id
		self._cls_id = cls_id
		
	def get_drop_action(self, src_parent, src_data, tgt_data):
		
		if src_parent == "external":
			if self._model.is_url_image(src_data["value"]):
				return DropActions.ADD_RESOURCE
			return None
		if ("image" in src_data) and src_data["image"]:
			return DropActions.ADD_RESOURCE
		return None
	
	def on_selection_changed(self):
		
		pass
	
	def on_activated(self):
		
		pass

class PrototypeImageForm(PrototypeForm):
	
	def __init__(self, parent_view, **kwargs):
		
		self.photoList = None
		self.drawingList = None
		
		super(PrototypeImageForm, self).__init__(parent_view, **kwargs)
	
	def clear_images_relations(self):
		
		self.clear_relations()
		self.photoList.clear()
		self.drawingList.clear()
		self.update_image_states()
	
	def reset(self):
		
		self.photoList.clear()
		self.drawingList.clear()
		super(PrototypeImageForm, self).reset()
	
	def update_buttons(self):
		
		self.buttonDeletePhoto.setEnabled(len(self.photoList.selectedIndexes()) > 0)
		self.buttonDeleteDrawing.setEnabled(len(self.drawingList.selectedIndexes()) > 0)
	
	def update_image_states(self):
		
		images_enabled = (not self._obj_id is None)
		self.photoList.setEnabled(images_enabled)
		self.drawingList.setEnabled(images_enabled)
	
	def set_up_images(self):
		
		self.photoList = ImageList(self._parent_view)
		self.drawingList = ImageList(self._parent_view)
		self.photoList.set_model(self._model)
		self.drawingList.set_model(self._model)
		self.photoFrame.layout().insertWidget(1, self.photoList)
		self.drawingFrame.layout().insertWidget(1, self.drawingList)
		
		for lst in [self.photoList, self.drawingList]:
			lst.itemActivated.connect(self.on_image_activated)
			lst.itemSelectionChanged.connect(self.on_image_selection_changed)
		
	def load_data(self):
		
		super(PrototypeImageForm, self).load_data()
		
		if not self.photoList is None:
			self.photoList.clear()
			self.drawingList.clear()
			self.update_images()
			self.update_image_states()
	
	def update_images(self):
		
		n_found = 0
		descr_ids = {} # {descr_name: [cls_id, ...], ...}
		for descr_name, lst, frame in [["Photo", self.photoList, self.photoFrame], ["Drawing", self.drawingList, self.drawingFrame]]:			
			descr_ids[descr_name] = []
			found = False
			for thumbnail, path, filename, rel_id, cls_id in self._model.get_images(self._obj_id, descr_name):
				descr_ids[descr_name].append(cls_id)
				found = True
				item = QtWidgets.QListWidgetItem()
				data = dict(
					obj_id = self._obj_id,
					cls_id = cls_id,
					rel_id = rel_id,
					value = path,
					storage_type = Resources.RESOURCE_ONLINE,
					path = path,
					filename = filename,
					thumbnail = thumbnail,
					read_only = True,
					image = True,
					geometry = False,
					obj3d = False,
				)
				item.setData(QtCore.Qt.UserRole, dict(parent = self.__class__.__name__, data = data))
				item.setData(QtCore.Qt.DisplayRole, filename)
				item.setData(QtCore.Qt.DecorationRole, QtGui.QIcon(thumbnail))
				item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsSelectable)
				lst.addItem(item)
			if found:
				n_found += 1
				lst.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			else:
				lst.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		if not n_found:
			for lst in [self.photoList, self.drawingList]:
				lst.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		
		for descr_name, lst in [["Photo", self.photoList], ["Drawing", self.drawingList]]:
			n = 1
			while True:
				cls_id = self._model.get_descr_id("%s_%d" % (descr_name, n))
				if not cls_id in descr_ids[descr_name]:
					break
				n += 1
			lst.set_obj_cls(self._obj_id, cls_id)
		
	def on_set_model(self):
		
		super(PrototypeImageForm, self).on_set_model()
		
		self.set_up_images()
	
	def on_store_changed(self, ids):
		
		super(PrototypeImageForm, self).on_store_changed(ids)
		
		if not self.photoList is None:
			self.photoList.clear()
			self.drawingList.clear()
			self.update_images()
	
	def on_submit(self):
	
		pass
	
	def on_reset(self):
		
		pass
	
	def on_close(self):
		
		pass
	
	def on_delete(self, lst):
		
		rel_id = None
		for idx in lst.selectedIndexes():
			rel_id = lst.item(idx.row()).data(QtCore.Qt.UserRole)["data"]["rel_id"]
			break
		if rel_id:
			self._model.delete_image(rel_id)
	
	@QtCore.pyqtSlot()
	def on_buttonDeletePhoto_clicked(self):
		
		self.on_delete(self.photoList)
	
	@QtCore.pyqtSlot()
	def on_buttonDeleteDrawing_clicked(self):
		
		self.on_delete(self.drawingList)
	
	def on_image_activated(self, *args):
		
		rel_id = None
		for idx in self.photoList.selectedIndexes():
			rel_id = self.photoList.item(idx.row()).data(QtCore.Qt.UserRole)["data"]["rel_id"]
		if rel_id:
			self._parent_view.open_resource(self._obj_id, rel_id)
	
	def on_image_selection_changed(self, *args):
		
		self.update_buttons()
	
	