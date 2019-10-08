from deposit import Broadcasts
from deposit.DModule import (DModule)

from deposit.commander.Model import (Model)

from deposit.commander.toolbar._Toolbar import (Toolbar)
from deposit.commander.dialogs._Dialogs import (Dialogs)
from deposit.commander.menu._Menu import (Menu)
from deposit.commander.Registry import (Registry)

from deposit import res

from deposit.commander.navigator._Navigator import (Navigator)
from deposit.commander.MdiArea import (MdiArea)
from deposit.commander.StatusBar import (StatusBar)
from deposit.commander.QueryToolbar import (QueryToolbar)
from deposit.commander.usertools._UserTools import (UserTools)

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class View(DModule, QtWidgets.QMainWindow):

	def __init__(self, model, *args):

		self.model = model
		self.args = args
		self.populate_thread = None
		self.registry = None
		
		self.navigator = None
		self.mdiarea = None

		self.toolbar = None
		self.menu = None
		self.dialogs = None
		
		self.querytoolbar = None
		self.usertools = None
		self.statusbar = None

		self._broadcast_timer = None

		DModule.__init__(self)
		QtWidgets.QMainWindow.__init__(self)

		self.set_up()

	def set_up(self):
		
		update_info = True
		if self.model is None:
			self.model = Model(self, *self.args)
			update_info = False
		
		self.registry = Registry("Deposit")
		
		self.stop_broadcasts()
		
		self.central_widget = QtWidgets.QWidget(self)
		self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
		self.central_layout.setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(self.central_widget)
		
		self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.central_layout.addWidget(self.splitter)
		
		self.navigator = Navigator(self.model, self)
		self.splitter.addWidget(self.navigator)
		self.mdiarea = MdiArea(self.model, self)
		self.splitter.addWidget(self.mdiarea)

		self.toolbar = Toolbar(self.model, self)
		self.menu = Menu(self.model, self)
		self.dialogs = Dialogs(self.model, self)
		
		self.querytoolbar = QueryToolbar(self.model, self)
		self.usertools = UserTools(self.model, self)
		self.statusbar = StatusBar(self.model, self)
		self.setStatusBar(self.statusbar)

		self.resume_broadcasts()
		
		self.setWindowIcon(self.get_icon("dep_cube.svg"))
		self.set_title()
		self.setStyleSheet("font: 14px;")
		
		self.menu.load_recent()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_LOCAL_FOLDER_CHANGED, self.on_local_folder_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)
		self.connect_broadcast(Broadcasts.STORE_SAVE_FAILED, self.on_save_failed)
		self.set_on_broadcast(self.on_broadcast)

		self._broadcast_timer = QtCore.QTimer()
		self._broadcast_timer.setSingleShot(True)
		self._broadcast_timer.timeout.connect(self.on_broadcast_timer)
		
		if update_info:
			self.update_model_info()
	
	def get_icon(self, name):

		path = os.path.join(os.path.dirname(res.__file__), name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		raise Exception("Could not load icon", name)

	def set_title(self, name = None):

		title = "Deposit"
		if name is None:
			self.setWindowTitle(title)
		else:
			self.setWindowTitle("%s - %s" % (name, title))

	def update_model_info(self):

		texts = []
		if self.model.identifier:
			self.set_title(os.path.split(str(self.model.identifier))[-1].strip("#"))
			texts.append("Database Identifier: <b>%s</b>" % (str(self.model.identifier)))
		if self.model.local_folder:
			texts.append("Local Folder: <b>%s</b>" % (str(self.model.local_folder)))
		if (not self.model.data_source is None) and (not self.model.data_source.connstr is None):
			texts.append("Connect String: <b>%s</b>" % (str(self.model.data_source.connstr)))
		if texts:
			self.mdiarea.set_background_text("".join([("<p>%s</p>" % text) for text in texts]))
		else:
			self.mdiarea.set_background_text("")

	def save(self):

		if self.model.data_source is None:

			directory = ""
			if not self.model.local_folder is None:
				directory = as_url(self.model.local_folder)
			url, format = QtWidgets.QFileDialog.getSaveFileUrl(self, caption="Save Database As", filter="JSON (*.json)", directory=directory)
			url = str(url.toString())
			if url:
				ds = None
#				if format == "Resource Description Framework (*.rdf)":
#					ds = self.model.datasources.RDFGraph(url=url)
				if format == "JSON (*.json)":
					ds = self.model.datasources.JSON(url=url)
				if (not ds is None) and ds.save():
					self.model.set_datasource(ds)
					self.menu.add_recent_url(url)

		else:
			if (self.model.data_source.name == "DB") and (not self.model.data_source.identifier):
				self.dialogs.open("SetIdentifier", True)
				return
			self.model.save()
			self.menu.add_recent_db(self.model.data_source.identifier, self.model.data_source.connstr)
	
	def query(self, querystr):
		
		querystr = querystr.strip()
		if querystr:
			if querystr.lower().startswith("select "):
				self.mdiarea.create("Query", querystr)
			else:
				self.model.query(querystr)
	
	def on_data_source_changed(self, args):
		
		self.update_model_info()
	
	def on_local_folder_changed(self, *args):
		
		self.update_model_info()
		reply = QtWidgets.QMessageBox.question(self, "Localise Resources", "Store all resources in the new Local Folder?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			self.model.localise_resources(force = True)
	
	def on_saved(self, args):
		
		print("Database Saved")
		self.statusbar.message("Database Saved")
	
	def on_save_failed(self, args):
		
		print("Saving failed!")
		self.statusbar.message("Saving failed!")

	def on_broadcast(self, signals):

		if (Broadcasts.STORE_SAVED in signals) or (Broadcasts.STORE_SAVE_FAILED in signals):
			self.process_broadcasts()
		else:
			self._broadcast_timer.start(100)

	def on_broadcast_timer(self):

		self.process_broadcasts()

	def closeEvent(self, event):

		if isinstance(self.model, Model):
			if not self.model.is_saved():
				reply = QtWidgets.QMessageBox.question(self, "Exit", "Save changes to database?",
													   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
				if reply == QtWidgets.QMessageBox.Yes:
					self.save()
				elif reply == QtWidgets.QMessageBox.No:
					pass
				else:
					event.ignore()

			if not self.populate_thread is None:
				self.populate_thread.terminate()
				self.populate_thread.wait()
			self.menu.save_recent()
			self.mdiarea.close_all()
			self.usertools.on_close()
			self.model.on_close()

		else:  # Commander started with an external Model
			if not self.populate_thread is None:
				self.populate_thread.terminate()
				self.populate_thread.wait()
			self.mdiarea.close_all()
			self.usertools.on_close()

