from PyQt5 import (QtWidgets, QtCore)

class RelationsView(QtWidgets.QWidget):
	
	def __init__(self):
		
		super(RelationsView, self).__init__()
		
		self._layout = QtWidgets.QVBoxLayout()
		self._items = [] # [QueryView, ...]
		self._labels = []
		
		self._layout.setContentsMargins(0, 0, 0, 0)
		self._layout.setSpacing(0)
		self.setLayout(self._layout)
	
	def items(self):
		
		return self._items
	
	def set_items(self, items):
		# items = [[widget, label], ...]
		
		# get visibility of current items
		was_visible = {} # {label: True/False, ...}
		for i in range(len(self._labels)):
			if not self._labels[i] is None:
				was_visible[self._labels[i]] = self._layout.itemAt(i * 2 + 1).widget().isVisible() 
		
		for i in reversed(range(self._layout.count())):
			item = self._layout.itemAt(i)
			if item.widget():
				item.widget().setParent(None)
			else:
				self._layout.removeItem(item)
		self._items = []
		self._labels = []
		for i in range(len(items)):
			widget, label = items[i]
			self._items.append(widget)
			self._labels.append(label)
			button = QtWidgets.QToolButton()
			button.setText(label)
			button.setArrowType(QtCore.Qt.DownArrow)
			button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
			button.setAutoRaise(True)
			button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
			button.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
			button.clicked.connect(self.on_buttonContainer)
			button._idx = i
			
			button_query = QtWidgets.QToolButton()
			button_query.setText("Query")
			button_query.setArrowType(QtCore.Qt.RightArrow)
			button_query.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
			button_query.setAutoRaise(True)
			button_query.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
			button_query.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
			button_query.clicked.connect(self.on_buttonQuery)
			button_query._idx = i
			
			button_layout = QtWidgets.QHBoxLayout()
			button_layout.setContentsMargins(0, 0, 0, 0)
			button_layout.addWidget(button)
			button_layout.addWidget(button_query)
			
			button_widget = QtWidgets.QWidget()
			button_widget.setLayout(button_layout)
			
			self._layout.addWidget(button_widget)
			self._layout.addWidget(widget)
			
			if (label in was_visible) and not was_visible[label]:
				widget.setVisible(False)
				button.setArrowType(QtCore.Qt.RightArrow)
	
	def on_buttonContainer(self):
		
		sender = self.sender()
		idx = sender._idx
		widget = self._layout.itemAt(idx * 2 + 1).widget()
		visible = not widget.isVisible()
		widget.setVisible(visible)
		if visible:
			sender.setArrowType(QtCore.Qt.DownArrow)
		else:
			sender.setArrowType(QtCore.Qt.RightArrow)
	
	def on_buttonQuery(self):
		
		sender = self.sender()
		idx = sender._idx
		widget = self._layout.itemAt(idx * 2 + 1).widget()
		widget._parent_view.open_query(widget._model.query_str())

