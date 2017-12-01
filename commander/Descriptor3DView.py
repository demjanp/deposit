from deposit.commander.PrototypeList import PrototypeList
from deposit.commander.ObjectFrame import ObjectFrame
from deposit.commander.DropActions import DropActions
from deposit.DLabel import (id_to_name)
from PyQt5 import (uic, QtCore, QtWidgets, QtGui)
from PyQt5 import (Qt3DCore, Qt3DRender, Qt3DExtras, Qt3DInput)
import os
import sys
from urllib.parse import urlparse

class Descriptor3DView(PrototypeList, *uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "Descriptor3D.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.ui")):
	
	def __init__(self, parent_view):
		
		super(Descriptor3DView, self).__init__(parent_view)
		self.setupUi(self)
		
		self.headerFrame = QtWidgets.QFrame()
		self.headerFrame.setLayout(QtWidgets.QHBoxLayout())
		self.objectFrame = ObjectFrame(self)
		self.headerFrame.layout().setContentsMargins(3, 3, 3, 3)
		self.headerFrame.layout().addWidget(self.objectFrame)
		self.headerFrame.layout().addStretch()
		self.verticalLayout.insertWidget(0, self.headerFrame)
	
	def _populate(self):
		
		if self._model.has_store():
			data = self._model.data()
			self.objectFrame.set_object(data["data"]["obj_id"])
			path, filename, storage_type = self._model.path()
			if path:
				self.set_title("obj(%s).%s = %s" % (id_to_name(data["data"]["obj_id"]), self._model.descriptor_name(), filename))
				window = Window3D(path, self._model._parent_model.store)
				container = self.window().createWindowContainer(window, self.frame)
				self.frame.layout().addWidget(container)
				window.show()
	
	def set_status(self, text, timeout = 0):
		
		self.statusBar.showMessage(text, timeout)
	
	def on_set_model(self):
		
		self._populate()
	
	def on_store_changed(self, ids):
		# TODO close if changed
		
		if ids:
			data = self._resource_item.data(QtCore.Qt.UserRole)
			rel_id = data["data"]["rel_id"]
			obj_id = data["data"]["obj_id"]
			uri = data["data"]["value"]
			if (rel_id in ids["updated"]) or (obj_id in ids["updated"]) or (uri in ids["updated"]):
				pass
				# TODO close if changed
		else:
			pass
			# TODO close if changed
	
	def on_activated(self, item):
		
		data = item.data(QtCore.Qt.UserRole)
		if data["parent"] == "ObjectFrame":
			self._parent_view.open_object(data["data"]["obj_id"])
			return
	
	def on_changed(self, item):
		# TODO
		
		pass
	
	def on_actionResetZoom_triggered(self, state):
		# TODO zoom
		
		pass
	
	def hasFocus(self):
		# TODO has focus
		
		return False
	
	def showEvent(self, event):
		# TODO adjust 3d view
		
		super(Descriptor3DView, self).showEvent(event)
		pass
	
class Window3D(Qt3DExtras.Qt3DWindow):
	
	def __init__(self, path, store):
		
		self._path = path
		self._store = store
		self._scene = None
		
		super(Window3D, self).__init__()
		self._populate()
	
	def _populate(self):
		
		path_mtl, path_texture = self._store.resources.material_3d(self._path)
		x_min, x_max, y_min, y_max, z_min, z_max = self._store.file.obj.get_extent(self._path)
		sx = x_max - x_min
		sy = y_max - y_min
		sz = z_max - z_min
		scale = 10 / max(sx, sy, sz)
		
		self._scene = Qt3DCore.QEntity()
		
		if path_texture:
			textureImage = Qt3DRender.QTextureImage()
			textureImage.setSource(QtCore.QUrl.fromLocalFile(path_texture))
			
			material = Qt3DExtras.QDiffuseMapMaterial(self._scene)
			material.diffuse().addTextureImage(textureImage)
			material.setAmbient(QtGui.QColor(255, 255, 255, 255))
			material.setShininess(0)
		else:
			material = Qt3DExtras.QPhongMaterial(self._scene)
			material.setAmbient(QtGui.QColor(140, 140, 140, 255))
			material.setShininess(0)
			
		objEntity = Qt3DCore.QEntity(self._scene)
		objMesh = Qt3DRender.QMesh()
		objMesh.setSource(QtCore.QUrl.fromLocalFile(self._path))
		
		objTransform = Qt3DCore.QTransform()
		objTransform.setScale3D(QtGui.QVector3D(scale, scale, scale))
		objTransform.setTranslation(QtGui.QVector3D((-x_min - (sx / 2)) * scale, (-y_min - (sy / 2)) * scale, (-z_min - (sz / 2)) * scale))
		
		objEntity.addComponent(objMesh)
		objEntity.addComponent(objTransform)
		objEntity.addComponent(material)

		self.setRootEntity(self._scene)
		camera = self.camera()
		camera.lens().setPerspectiveProjection(45.0, 16.0/9.0, 0.1, 1000.0)
		camera.setPosition(QtGui.QVector3D(0, 0, 10))
		camera.setViewCenter(QtGui.QVector3D(0, 0, 0))
		
		camController = Qt3DExtras.QOrbitCameraController(self._scene)
		camController.setLinearSpeed(50.0)
		camController.setLookSpeed(180.0)
		camController.setCamera(camera)

