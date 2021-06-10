
from PySide2 import (QtWidgets, QtCore, QtGui, QtPrintSupport)
import weakref
import math

NODE_TYPE = QtWidgets.QGraphicsItem.UserType + 1
EDGE_TYPE = QtWidgets.QGraphicsItem.UserType + 2

class Node(QtWidgets.QGraphicsItem):
	
	def __init__(self, node_id, label = ""):
		
		self.node_id = node_id
		self.label = str(label)
		self.edges = []  # [Edge, ...]
		self.font = QtGui.QFont("Calibri", 16)
		self.label_w = 0
		
		QtWidgets.QGraphicsItem.__init__(self)
		
		if self.label != "":
			rect = QtGui.QFontMetrics(self.font).boundingRect(self.label)
			self.label_w = rect.width()
		
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
		self.setCacheMode(self.DeviceCoordinateCache)
		self.setZValue(-1)
	
	def type(self):
		
		return NODE_TYPE
	
	def add_edge(self, edge):
		
		self.edges.append(weakref.ref(edge))
		edge.adjust()
	
	def boundingRect(self):
		
		adjust = 2		
		return QtCore.QRectF(-20 - adjust, -20 - adjust, max(45 + self.label_w, 40) + 3 + adjust, 43 + adjust)
	
	def center(self):
		
		return QtCore.QPointF(0, 0)
	
	def shape(self):
		
		path = QtGui.QPainterPath()
		path.addEllipse(-20, -20, 40, 40)
		return path
	
	def paint(self, painter, option, widget):
		
		pen_width = 0
		if option.state & QtWidgets.QStyle.State_Sunken:
			pen_width = 2
		if option.state & QtWidgets.QStyle.State_Selected:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.gray))
		else:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
		painter.setPen(QtGui.QPen(QtCore.Qt.black, pen_width))
		painter.drawEllipse(-20, -20, 40, 40)
		if self.label != "":
			painter.setFont(self.font)
			painter.drawText(25, 8, self.label)
	
	def itemChange(self, change, value):
		
		if change == QtWidgets.QGraphicsItem.ItemPositionChange:
			for edge in self.edges:
				edge().adjust()
		
		return QtWidgets.QGraphicsItem.itemChange(self, change, value)
	
	def mousePressEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mousePressEvent(self, event)
	
	def mouseReleaseEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

class NodeWithAttributes(QtWidgets.QGraphicsItem):
	
	def __init__(self, node_id, label = "", descriptors = []):
		
		self.node_id = node_id
		self.label = str(label)
		self.descriptors = []
		self.edges = []  # [Edge, ...]
		self.font = QtGui.QFont("Calibri", 14)
		self.label_w = 0
		self.label_h = 0
		self.descriptor_w = 0
		self.descriptor_h = 0
		self.selection_polygon = None
		self.selection_shape = None
		self.text_padding = 3
		
		QtWidgets.QGraphicsItem.__init__(self)
		
		for name, value in descriptors:
			if value:
				self.descriptors.append("%s: %s" % (name, value))
			else:
				self.descriptors.append(name)
		
		self.adjust()
		
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
		self.setCacheMode(self.DeviceCoordinateCache)
		self.setZValue(-1)
	
	def type(self):
		
		return NODE_TYPE
	
	def adjust(self):
		
		adjust_w = 2
		adjust_h = 0
		
		if self.label != "":
			rect = QtGui.QFontMetrics(self.font).boundingRect(self.label)
			self.label_w = rect.width() + adjust_w
			self.label_h = rect.height() + adjust_h
		
		self.descriptor_w = 0
		self.descriptor_h = 0
		for text in self.descriptors:
			rect = QtGui.QFontMetrics(self.font).boundingRect(text)
			self.descriptor_w = max(self.descriptor_w, rect.width() + adjust_w)
			self.descriptor_h = max(self.descriptor_h, rect.height() + adjust_h)
		
		w = max(self.label_w, self.descriptor_w) + 2*self.text_padding
		h = self.label_h + 2*self.text_padding + len(self.descriptors)*(self.descriptor_h + self.text_padding) + self.text_padding
		
		self.selection_polygon = QtGui.QPolygonF(QtCore.QRectF(0, 0, w, h))
		self.selection_shape = QtGui.QPainterPath()
		self.selection_shape.addPolygon(self.selection_polygon)
	
	def add_edge(self, edge):
		
		self.edges.append(weakref.ref(edge))
		edge.adjust()
	
	def boundingRect(self):
		
		return self.selection_polygon.boundingRect()
	
	def center(self):
		
		return self.boundingRect().center()
	
	def shape(self):
		
		return self.selection_shape
	
	def paint(self, painter, option, widget):
		
		adjust_y = -2
		
		pen_width = 0
		if option.state & QtWidgets.QStyle.State_Sunken:
			pen_width = 2
		
		y = self.label_h + 2*self.text_padding + adjust_y
		rect = self.selection_polygon.boundingRect()
		
		painter.setPen(QtCore.Qt.NoPen)
		painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
		painter.drawPath(self.selection_shape)
		
		painter.setPen(QtCore.Qt.NoPen)
		if option.state & QtWidgets.QStyle.State_Selected:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.darkGray))
		else:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.lightGray))
		painter.drawRect(0, 0, rect.width(), y)
		
		painter.setPen(QtGui.QPen(QtCore.Qt.black, pen_width))
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.drawLine(0, y, rect.width(), y)
		painter.drawPath(self.selection_shape)
		
		painter.setFont(self.font)
		
		if self.label != "":
			painter.drawText(self.text_padding, self.label_h + adjust_y, self.label)
		
		for n, text in enumerate(self.descriptors):
			painter.drawText(self.text_padding, y + (n + 1)*(self.descriptor_h + self.text_padding) + adjust_y, text)
	
	def itemChange(self, change, value):
		
		if change == QtWidgets.QGraphicsItem.ItemPositionChange:
			for edge in self.edges:
				edge().adjust()
		
		return QtWidgets.QGraphicsItem.itemChange(self, change, value)
	
	def mousePressEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mousePressEvent(self, event)
	
	def mouseReleaseEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

class NodeWithSimpleAttributes(QtWidgets.QGraphicsItem):
	
	def __init__(self, node_id, descriptors = []):
		
		self.node_id = node_id
		self.descriptors = []
		self.edges = []  # [Edge, ...]
		self.font = QtGui.QFont("Calibri", 14)
		self.descriptor_w = 0
		self.descriptor_h = 0
		self.selection_polygon = None
		self.selection_shape = None
		self.text_padding = 3
		
		QtWidgets.QGraphicsItem.__init__(self)
		
		for _, value in descriptors:
			self.descriptors.append(str(value))
		
		self.adjust()
		
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
		self.setCacheMode(self.DeviceCoordinateCache)
		self.setZValue(-1)
	
	def type(self):
		
		return NODE_TYPE
	
	def adjust(self):
		
		adjust_w = 2
		adjust_h = 0
		
		self.descriptor_w = 0
		self.descriptor_h = 0
		for text in self.descriptors:
			rect = QtGui.QFontMetrics(self.font).boundingRect(text)
			self.descriptor_w = max(self.descriptor_w, rect.width() + adjust_w)
			self.descriptor_h = max(self.descriptor_h, rect.height() + adjust_h)
		
		w = self.descriptor_w + 2*self.text_padding
		h = len(self.descriptors)*(self.descriptor_h + self.text_padding) + self.text_padding
		
		self.selection_polygon = QtGui.QPolygonF(QtCore.QRectF(0, 0, w, h))
		self.selection_shape = QtGui.QPainterPath()
		self.selection_shape.addPolygon(self.selection_polygon)
	
	def add_edge(self, edge):
		
		self.edges.append(weakref.ref(edge))
		edge.adjust()
	
	def boundingRect(self):
		
		return self.selection_polygon.boundingRect()
	
	def center(self):
		
		return self.boundingRect().center()
	
	def shape(self):
		
		return self.selection_shape
	
	def paint(self, painter, option, widget):
		
		adjust_y = -2
		
		pen_width = 0
		if option.state & QtWidgets.QStyle.State_Sunken:
			pen_width = 2
		
		painter.setPen(QtCore.Qt.NoPen)
		if option.state & QtWidgets.QStyle.State_Selected:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.lightGray))
		else:
			painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
		
		painter.setPen(QtGui.QPen(QtCore.Qt.black, pen_width))
		
		painter.drawPath(self.selection_shape)
		
		y = adjust_y
		
		painter.setFont(self.font)
		
		for n, text in enumerate(self.descriptors):
			painter.drawText(self.text_padding, y + (n + 1)*(self.descriptor_h + self.text_padding) + adjust_y, text)
	
	def itemChange(self, change, value):
		
		if change == QtWidgets.QGraphicsItem.ItemPositionChange:
			for edge in self.edges:
				edge().adjust()
		
		return QtWidgets.QGraphicsItem.itemChange(self, change, value)
	
	def mousePressEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mousePressEvent(self, event)
	
	def mouseReleaseEvent(self, event):
		
		self.update()
		QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

class Edge(QtWidgets.QGraphicsItem):
	
	def __init__(self, source, target, label = "", color = None):
		
		self.label = label
		self.color = QtCore.Qt.gray if color is None else color
		self.source = weakref.ref(source)
		self.target = weakref.ref(target)
		
		self.arrow_size = 20.0
		self.font = QtGui.QFont("Calibri", 16)
		self.source_point = QtCore.QPointF()
		self.target_point = QtCore.QPointF()
		self.label_w = 0
		self.label_h = 0
		self.line = None
		self.selection_polygon = None
		self.selection_shape = None
		
		QtWidgets.QGraphicsItem.__init__(self)
		
		if self.label != "":
			rect = QtGui.QFontMetrics(self.font).boundingRect(self.label)
			self.label_w = rect.width()
			self.label_h = rect.height()
		
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
		self.setZValue(-2)
		
		self.source().add_edge(self)
		self.target().add_edge(self)
		self.adjust()
	
	def type(self):
		
		return EDGE_TYPE
	
	def adjust(self):
		
		self.selection_polygon = QtGui.QPolygonF()
		
		if not self.source() or not self.target():
			return
		
		self.line = QtCore.QLineF(self.mapFromItem(self.source(), self.source().center()), self.mapFromItem(self.target(), self.target().center()))
		length = self.line.length()
		
		if length == 0:
			return
		
		self.prepareGeometryChange()
		self.source_point = self.line.p1()
		self.target_point = self.line.p2()
		
		selection_offset = 20
		rad_angle = self.line.angle() * math.pi / 180
		dx = selection_offset * math.sin(rad_angle)
		dy = selection_offset * math.cos(rad_angle)
		offset1 = QtCore.QPointF(dx, dy)
		offset2 = QtCore.QPointF(-dx, -dy)
		self.selection_polygon.append(self.line.p1() + offset1)
		self.selection_polygon.append(self.line.p1() + offset2)
		self.selection_polygon.append(self.line.p2() + offset2)
		self.selection_polygon.append(self.line.p2() + offset1)
		
		self.selection_shape = QtGui.QPainterPath()
		self.selection_shape.addPolygon(self.selection_polygon)
	
	def boundingRect(self):
		
		rect = self.selection_polygon.boundingRect()
		if self.label != "":
			self.label_w
			self.label_h
			x = (self.source_point.x() + self.target_point.x()) / 2
			y = (self.source_point.y() + self.target_point.y()) / 2
			x = min(rect.x(), x - self.label_w / 2 - 4)
			y = min(rect.y(), y - self.label_h / 2 - 4)
			w = max(rect.width(), self.label_w + 4)
			h = max(rect.height(), self.label_h + 4)
			return QtCore.QRectF(x, y, w, h)
		return rect
	
	def shape(self):
		
		return self.selection_shape
	
	def paint(self, painter, option, widget):
		
		if not self.source() or not self.target():
			return
		
		pen_width = 1
		if option.state & QtWidgets.QStyle.State_Selected:
			pen_width = 2
		
		pen = QtGui.QPen(self.color, pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
		pen.setCosmetic(True)
		painter.setPen(pen)
		painter.drawLine(self.line)
		
		length = self.line.length()
		if length:
			angle = math.acos(self.line.dx() / length)
		else:
			angle = 0
		if self.line.dy() >= 0:
			angle = 2*math.pi - angle
		
		arrow_pos = self.line.pointAt(0.6)
		
		arrow_p1 = arrow_pos + QtCore.QPointF(math.sin(angle - math.pi / 3) * self.arrow_size, math.cos(angle - math.pi / 3) * self.arrow_size)
		arrow_p2 = arrow_pos + QtCore.QPointF(math.sin(angle - math.pi + math.pi / 3) * self.arrow_size, math.cos(angle - math.pi + math.pi / 3) * self.arrow_size)
		
		painter.setBrush(self.color)
		painter.drawPolygon(QtGui.QPolygonF([arrow_pos, arrow_p1, arrow_p2]))
		if self.label != "":
			painter.setFont(self.font)
			painter.setPen(QtGui.QPen(QtCore.Qt.black, pen_width))
			text_pos = self.line.center()
			x = text_pos.x()
			y = text_pos.y()
			painter.drawText(x - self.label_w / 2, y + self.label_h / 4, self.label)

class GraphVisView(QtWidgets.QGraphicsView):
	
	activated = QtCore.Signal(object)
	selected = QtCore.Signal()
	
	def __init__(self):
		
		self._nodes = {}  # {node_id: Node, ...}
		self._edges = []  # [Edge, ...]
		self._mouse_prev = None
		self._show_attributes = False
		
		QtWidgets.QGraphicsView.__init__(self)
		
		scene = QtWidgets.QGraphicsScene(self)
		scene.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)
		self.setScene(scene)
		self.setRenderHint(QtGui.QPainter.Antialiasing)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
		self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
		
		self.setMinimumSize(400, 400)
		
		scene.selectionChanged.connect(self.on_selected)
	
	def clear(self):
		
		self.scene().clear()
		self.setSceneRect(QtCore.QRectF())
		self._nodes.clear()
		self._edges.clear()
	
	def reset_scene(self):
		
		rect = self.scene().itemsBoundingRect().marginsAdded(QtCore.QMarginsF(10, 10, 10, 10))
		self.setSceneRect(rect)
		self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
	
	def set_data(self, nodes, edges, attributes, positions, show_attributes = 0):
		# nodes = {node_id: label, ...}
		# edges = [[source_id, target_id, label], ...] or [[source_id, target_id, label, color], ...]
		# attributes = {node_id: [(name, value), ...], ...}
		# positions = {node_id: (x, y), ...}
		# show_attributes = 0 (none) / 1 (values only) / 2 (node_id, attribute names and values)
		
		self._show_attributes = show_attributes
		self.clear()
		for node_id in nodes:
			if self._show_attributes == 2:
				self._nodes[node_id] = NodeWithAttributes(node_id, nodes[node_id], attributes[node_id] if node_id in attributes else [])
			elif self._show_attributes == 1:
				self._nodes[node_id] = NodeWithSimpleAttributes(node_id, attributes[node_id] if node_id in attributes else [])
			else:
				self._nodes[node_id] = Node(node_id, nodes[node_id])
			self.scene().addItem(self._nodes[node_id])
			x, y = positions[node_id]
			if self._show_attributes:
				self._nodes[node_id].setPos(x*4, y*4)
			else:
				self._nodes[node_id].setPos(x*2, y*2)
		for row in edges:
			if len(row) == 3:
				source_id, target_id, label = row
				color = None
			elif len(row) == 4:
				source_id, target_id, label, color = row
				if isinstance(color, str):
					try:
						color = getattr(QtCore.Qt, color)
					except:
						color = None
			else:
				raise Exception("Invalid edge format: %s" % (str(row)))
			if (source_id not in self._nodes) or (target_id not in self._nodes):
				continue
			self._edges.append(Edge(self._nodes[source_id], self._nodes[target_id], label, color))
			self.scene().addItem(self._edges[-1])
	
	def get_selected(self):
		
		nodes = []
		edges = []
		for item in self.scene().selectedItems():
			if item.type() == NODE_TYPE:
				nodes.append(item.node_id)
			elif item.type() == EDGE_TYPE:
				edges.append((item.source().node_id, item.target().node_id, item.label))
		return nodes, edges
	
	def get_positions(self):
		
		positions = {}
		for node_id in self._nodes:
			pos = self._nodes[node_id].pos()
			x, y = pos.x(), pos.y()
			if self._show_attributes:
				positions[node_id] = (x / 4, y / 4)
			else:
				positions[node_id] = (x / 2, y / 2)
		return positions
	
	def wheelEvent(self, event):
		
		self.scale_view(2**(event.delta() / 240.0))
	
	def scale_view(self, factor):
		
		self.scale(factor, factor)
	
	def save_pdf(self, path):
		
		self.scene().clearSelection()
		
		rect = self.scene().itemsBoundingRect().marginsAdded(QtCore.QMarginsF(10, 10, 10, 10))
		w, h = rect.width(), rect.height()	
		printer = QtPrintSupport.QPrinter()
		printer.setPageSize(QtGui.QPageSize(QtCore.QSize(w, h)))
		printer.setOrientation(QtPrintSupport.QPrinter.Portrait)
		printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
		printer.setOutputFileName(path)
		painter = QtGui.QPainter(printer)
		self.scene().render(painter, source = rect)
		painter.end()
	
	@QtCore.Slot()
	def on_selected(self):
		
		self.selected.emit()
	
	def mousePressEvent(self, event):
		
		if event.button() == QtCore.Qt.LeftButton:
			self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
			self.setCursor(QtCore.Qt.ArrowCursor)
		elif event.button() == QtCore.Qt.RightButton:
			self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
			self.setCursor(QtCore.Qt.OpenHandCursor)
			self._mouse_prev = (event.x(), event.y())
		
		QtWidgets.QGraphicsView.mousePressEvent(self, event)
	
	def mouseMoveEvent(self, event):
		
		if self._mouse_prev is not None:
			prev_point = self.mapToScene(*self._mouse_prev)
			new_point = self.mapToScene(event.pos())
			translation = new_point - prev_point
			self.translate(translation.x(), translation.y())
			self._mouse_prev = (event.x(), event.y())
		
		QtWidgets.QGraphicsView.mouseMoveEvent(self, event)
	
	def mouseReleaseEvent(self, event):
		
		self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
		self.setCursor(QtCore.Qt.ArrowCursor)
		self._mouse_prev = None
		
		QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)
	
	def mouseDoubleClickEvent(self, event):
		
		item = self.itemAt(event.pos())
		if item is None:
			return
		if item.type() == NODE_TYPE:
			self.activated.emit(item.node_id)
	