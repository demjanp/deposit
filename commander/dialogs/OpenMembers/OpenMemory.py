from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_path)

from PySide2 import (QtWidgets, QtCore, QtGui)
from deposit.store.Conversions import (as_identifier)

import os

class OpenMemory(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.label = QtWidgets.QLabel("Create a new database in memory.\n\n")
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		
		self.connect_button = QtWidgets.QPushButton("Create")
		self.connect_button.clicked.connect(self.on_connect)
		
		self.layout().addStretch()
		self.layout().addWidget(self.label)
		self.layout().addWidget(self.connect_button, alignment = QtCore.Qt.AlignCenter)
		self.layout().addStretch()
		
	def on_connect(self):
		
		self.model.clear()
		self.model.set_datasource(None)
		self.parent.close()

