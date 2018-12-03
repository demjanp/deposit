from deposit.DModule import (DModule)

from PyQt5 import (QtCore, QtWidgets, QtGui, QtSvg)

class ResourceItem(DModule):
	
	def __init__(self, parent):
		
		self.parent = parent

		DModule.__init__(self)

		self.setAcceptHoverEvents(True)
		self.setAcceptDrops(True)
		self.setZValue(0)
	
	def hoverEnterEvent(self, event):
		
		self.parent.on_mouse_enter()
	
	def hoverMoveEvent(self, event):
		
		self.parent.on_mouse_move(event.pos())
		super(ResourceItem, self).hoverMoveEvent(event)
	
	def hoverLeaveEvent(self, event):
		
		self.parent.on_mouse_leave()
	
#	def dragEnterEvent(self, event):
		
#		self.parent.dragEnterEvent(event)
	
#	def dragMoveEvent(self, event):
		
#		self.parent.dragMoveEvent(event)
	
#	def dropEvent(self, event):
		
#		self.parent.dropEvent(event)
	
	def mousePressEvent(self, event):
		
		self.parent.on_mouse_press(event.pos(), event.button())
		super(ResourceItem, self).mousePressEvent(event)
	
	def mouseReleaseEvent(self, event):
		
		self.parent.on_mouse_release(event.pos(), event.button())
		super(ResourceItem, self).mouseReleaseEvent(event)

class PixmapItem(ResourceItem, QtWidgets.QGraphicsPixmapItem):
	
	def __init__(self, parent, path):
		
		QtWidgets.QGraphicsPixmapItem.__init__(self, QtGui.QPixmap(path))
		ResourceItem.__init__(self, parent)

class SvgItem(ResourceItem, QtSvg.QGraphicsSvgItem):
	
	def __init__(self, parent, path):
		
		QtSvg.QGraphicsSvgItem.__init__(self, path)
		ResourceItem.__init__(self, parent)

