import deposit
from deposit import Broadcasts
from deposit.DModule import (DModule)

from deposit.commander.Model import (Model)

from deposit.commander.toolbar._Toolbar import (Toolbar)
from deposit.commander.dialogs._Dialogs import (Dialogs)
from deposit.commander.menu._Menu import (Menu)

from deposit.commander.navigator._Navigator import (Navigator)
from deposit.commander.MdiArea import (MdiArea)
from deposit.commander.StatusBar import (StatusBar)
from deposit.commander.QueryToolbar import (QueryToolbar)
from deposit.commander.plugins._Plugins import (Plugins)

from PyQt5 import (QtWidgets, QtCore, QtGui)
import os

class View(DModule, QtWidgets.QMainWindow):

	def __init__(self):

		self.model = None
		self.populate_thread = None

		self.navigator = None
		self.mdiarea = None

		self.toolbar = None
		self.menu = None
		self.dialogs = None
		
		self.plugins = None
		self.querytoolbar = None
		self.statusbar = None

		self._broadcast_timer = None

		DModule.__init__(self)
		QtWidgets.QMainWindow.__init__(self)

		self.set_up()

	def set_up(self):
		
		self.model = Model(self)
		
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
		
		self.plugins = Plugins(self.model, self)
		self.querytoolbar = QueryToolbar(self.model, self)
		self.statusbar = StatusBar(self.model, self)
		self.setStatusBar(self.statusbar)

		self.resume_broadcasts()
		
		self.setWindowIcon(self.get_icon("dep_cube.svg"))
		self.set_title()
		self.setStyleSheet("font: 14px;")
		
		self.menu.load_recent()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_LOCAL_FOLDER_CHANGED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)
		self.connect_broadcast(Broadcasts.STORE_SAVE_FAILED, self.on_save_failed)
		self.set_on_broadcast(self.on_broadcast)

		self._broadcast_timer = QtCore.QTimer()
		self._broadcast_timer.setSingleShot(True)
		self._broadcast_timer.timeout.connect(self.on_broadcast_timer)
	
	def get_icon(self, name):

		path = os.path.join(os.path.dirname(deposit.__file__), "commander", "res", name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		raise Exception("Could not load icon", name)

	def set_title(self, name = None):

		title = "Deposit_dev"
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
	
	def on_data_source_changed(self, args):
		
		self.update_model_info()
	
	def on_saved(self, args):
		
		print("Database Saved")
		self.statusbar.message("Database Saved")
	
	def on_save_failed(self, args):
		
		print("Saving failed!")
		self.statusbar.message("Saving failed!")

	def on_broadcast(self):

		self._broadcast_timer.start(100)

	def on_broadcast_timer(self):

		self.process_broadcasts()

	def closeEvent(self, event):
		
		if not self.populate_thread is None:
			self.populate_thread.terminate()
			self.populate_thread.wait()
		self.menu.save_recent()
		self.mdiarea.close_all()
		self.plugins.close_all()
		self.model.on_close()
	