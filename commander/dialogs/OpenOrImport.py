from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class OpenOrImport(Dialog):
	
	def title(self):
		
		return "Choose Action"
	
	def set_up(self, url):
		
		self.url = url
		
		self.setMinimumWidth(300)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		label = QtWidgets.QLabel("Choose an action with the Deposit database:")
		label.setAlignment(QtCore.Qt.AlignCenter)
		buttonbox = QtWidgets.QFrame()
		buttonbox.setLayout(QtWidgets.QHBoxLayout())
		button_open = QtWidgets.QPushButton("Open")
		button_open.clicked.connect(self.on_open)
		button_import = QtWidgets.QPushButton("Import")
		button_import.clicked.connect(self.on_import)
		buttonbox.layout().addStretch()
		buttonbox.layout().addWidget(button_open)
		buttonbox.layout().addWidget(button_import)
		buttonbox.layout().addStretch()
		
		self.layout().addWidget(label)
		self.layout().addWidget(buttonbox)
	
	def button_box(self):
		
		return False, False
	
	def on_open(self):
		
		self.model.load(self.url)
		self.view.menu.add_recent_url(self.url)
		self.close()
	
	def on_import(self):
		
		self.model.add_objects(self.url, None)
		self.close()
	
