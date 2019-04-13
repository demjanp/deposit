from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class DescriptorGraphicsView(Frame, QtWidgets.QGraphicsView):
	
	def __init__(self, model, view, parent):
	
		Frame.__init__(self, model, view, parent)
		QtWidgets.QGraphicsView.__init__(self)
		
		self.set_up()
	
	def set_up(self):
		
		self.scene = QtWidgets.QGraphicsScene()
		self.scene_rect = None
		
		self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
		self.setScene(self.scene)		
	
	def add_item(self, item):
		
		self.scene.addItem(item)
		self.zoom()
	
	def clear(self):
		
		self.scene.clear()
	
	def zoom(self, direction = None):
		
		if direction is None:
			rect = self.scene.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(10, 10, 10, 10))
			self.setSceneRect(rect)
			self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
		else:
			factor = 1
			if direction == 1:
				factor = 1.1
			elif direction == -1:
				factor = 0.9
			self.scale(factor, factor)
	
	def wheelEvent(self, event):
		
		d = event.angleDelta().y()
		if d > 0:
			self.zoom(1)
		elif d < 0:
			self.zoom(-1)
	
	def showEvent(self, event):
		
		self.zoom()
	
	def resizeEvent(self, event):
		
		if self.scene_rect is None:
			self.zoom()
			self.scene_rect = self.rect()
		else:
			new_rect = self.rect()
			factor = max(new_rect.width() / self.scene_rect.width(), new_rect.height() / self.scene_rect.height())
			self.scale(factor, factor)
			self.scene_rect = new_rect
	
	def mouseDoubleClickEvent(self, event):
		
		item = self.itemAt(event.pos())
		if item:
			self.parent.on_activated(item)
	
	def mouseReleaseEvent(self, event):
		
		self.parent.on_mouse_release(event.pos(), event.button())
		super(DescriptorGraphicsView, self).mouseReleaseEvent(event)

