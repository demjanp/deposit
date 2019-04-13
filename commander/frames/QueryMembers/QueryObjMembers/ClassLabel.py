from deposit.commander.frames._Frame import (Frame)

from PySide2 import (QtWidgets, QtCore, QtGui)

class ClassLabel(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, cls):
		
		self.cls = cls
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.label_icon = QtWidgets.QLabel()
		self.label_icon.setPixmap(self.view.get_icon("class.svg").pixmap(24, 24))
		self.label_text = QtWidgets.QLabel(self.cls)
		
		self.layout.addWidget(self.label_icon)
		self.layout.addWidget(self.label_text)
		self.setStyleSheet("QWidget {background-color : #dddddd;} QLabel {padding : 3px;}")
	
	def contextMenuEvent(self, event):
		
		menu = QtWidgets.QMenu(self)
		actionRemove = menu.addAction("Remove")
		action = menu.exec_(self.mapToGlobal(event.pos()))
		if action == actionRemove:
			self.parent.on_remove_class(self.cls)
