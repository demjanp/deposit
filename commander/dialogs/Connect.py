
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs.DataSource import (DataSource)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class Connect(DataSource):
	
	def title(self):
		
		return "Select Data Source"
	
	def creating_enabled(self):
		
		return True
	
	def logo(self):
		
		logo_frame = QtWidgets.QFrame()
		logo_frame.setLayout(QtWidgets.QVBoxLayout())
		logo_frame.layout().setContentsMargins(0, 0, 0, 0)
		
		logo = QtWidgets.QLabel()
		logo.setPixmap(QtGui.QPixmap("deposit/res/dep_installer.svg"))
		
		logo_frame.layout().addStretch()
		logo_frame.layout().addWidget(logo)
		logo_frame.layout().addStretch()
		
		return logo_frame
	
	def on_connect(self, identifier, connstr, local_folder = None, created = False):
		
		if identifier is None:
			self.model.clear()
			self.model.set_datasource(None)
		else:
			self.model.load(identifier, connstr)
			if local_folder:
				if created:
					self.model.set_local_folder(local_folder)
				elif self.model.local_folder != local_folder:
					reply = QtWidgets.QMessageBox.question(self, "Change Local Folder?", "Change Local Folder from %s to %s?" % (self.model.local_folder, local_folder), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
					if reply == QtWidgets.QMessageBox.Yes:
						self.model.set_local_folder(local_folder)
		self.close()

