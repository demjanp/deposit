
import deposit
from deposit import (__version__, __date__)
from deposit.commander.dialogs.DataSource import (DataSource)

from PySide2 import (QtWidgets, QtCore, QtGui)
import webbrowser
import os

class Connect(DataSource):
	
	def title(self):
		
		return "Select Data Source"
	
	def set_up(self, save = False):
		
		self.save = save
		
		DataSource.set_up(self)
	
	def creating_enabled(self):
		
		return True
	
	def logo(self):
		
		logo_frame = QtWidgets.QFrame()
		logo_frame.setLayout(QtWidgets.QVBoxLayout())
		logo_frame.layout().setContentsMargins(0, 0, 0, 0)
		logo_frame.layout().addStretch()
		logo_frame.layout().addWidget(ClickableLogo("deposit/res/dep_installer.svg", "https://github.com/demjanp/deposit", alignment = QtCore.Qt.AlignCenter))
		logo_frame.layout().addStretch()
		
		return logo_frame
	
	def on_connect(self, identifier, connstr, local_folder = None, created = False):
		
		ds_import = None
		if (len(self.model.objects) > 0) or (len(self.model.classes) > 0):
			
			do_import = self.save
			if not self.save:
				msgbox = QtWidgets.QMessageBox()
				msgbox.setWindowTitle("Import current data?")
				msgbox.setText("Import current data into new database?")
				button_import = msgbox.addButton("Import", QtWidgets.QMessageBox.YesRole)
				button_import.setToolTip("Import current data into the newly opened database.")
				button_no = msgbox.addButton("No", QtWidgets.QMessageBox.NoRole)
				button_no.setToolTip("Just open the new database, without importing.")
				button_cancel = msgbox.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
				msgbox.setIcon(QtWidgets.QMessageBox.Question)
				ret = msgbox.exec()
				if msgbox.clickedButton() == button_cancel:
					self.close()
					return
				do_import = (msgbox.clickedButton() == button_import)				
			
			if do_import:
				ds_import = dict(
					data_source_class = None,
					identifier = None,
					url = None,
					connstr = None,
					local_folder = self.model.local_folder,
					changed = self.model.changed,
					classes = self.model.classes.to_dict(), # {name: class data, ...}
					objects = self.model.objects.to_dict(), # {id: object data, ...}
					events = self.model.events.to_list(),
					user_tools = self.model.user_tools.to_list(),
					queries = self.model.queries.to_dict(),
				)
		
		if identifier is None:
			self.model.clear()
			self.model.set_datasource(None)
		else:
			self.model.load(identifier, connstr)
			if local_folder:
				if created:
					self.model.set_local_folder(local_folder, silent = True)
				elif self.model.local_folder != local_folder:
					reply = QtWidgets.QMessageBox.question(self, "Change Local Folder?", "Change Local Folder from %s to %s?" % (self.model.local_folder, local_folder), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
					if reply == QtWidgets.QMessageBox.Yes:
						self.model.set_local_folder(local_folder)
						self.model.save()
		
		if ds_import is not None:
			self.model.add_objects(ds_import, None, localise = True)
			if self.save:
				self.model.save()
		
		self.close()

class ClickableLogo(QtWidgets.QLabel):
	
	def __init__(self, image_path, link, *args, **kwargs):
		
		self.link = link
		
		QtWidgets.QLabel.__init__(self, *args, **kwargs)
		
		self.setPixmap(QtGui.QPixmap(image_path))
		self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
	
	def mousePressEvent(self, event):
		
		webbrowser.open(self.link)
		QtWidgets.QLabel.mousePressEvent(self, event)
	

