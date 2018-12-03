from deposit.commander.frames._Frame import (Frame)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class ObjectLabel(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent):
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.label_icon = QtWidgets.QLabel()
		self.label_icon.setPixmap(self.view.get_icon("object.svg").pixmap(24, 24))
		self.label_text = QtWidgets.QLabel("obj")
		
		self.layout.addWidget(self.label_icon)
		self.layout.addWidget(self.label_text)
		self.setStyleSheet("QWidget {background-color : #dddddd;} QLabel {padding : 3px;}")
	
	def populate_data(self, obj):
		
		self.label_text.setText(str(obj.id))

