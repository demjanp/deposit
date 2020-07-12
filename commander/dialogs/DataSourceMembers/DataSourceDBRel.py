from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_identifier)
from deposit.store.Store import (Store)

import os
from PySide2 import (QtWidgets, QtCore, QtGui)

class DataSourceDBRel(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		self._connstr_prev = None
		self._valid_db = False
		self._identifier = None
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.form = QtWidgets.QWidget()
		self.form.setLayout(QtWidgets.QFormLayout())
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.server_combo = QtWidgets.QComboBox()
		self.server_combo.setEditable(True)
		self.name_combo = QtWidgets.QComboBox()
		self.name_combo.setEditable(True)
		self.user_edit = QtWidgets.QLineEdit("")
		self.user_edit.textChanged.connect(self.update)
		self.pass_edit = QtWidgets.QLineEdit("")
		self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
		self.pass_edit.textChanged.connect(self.update)
		self.identifier_edit = QtWidgets.QLineEdit("")
		self.identifier_edit.textChanged.connect(self.update)
		self.local_folder_edit = QtWidgets.QLineEdit("")
		self.local_folder_edit.textChanged.connect(self.on_local_folder_edit)
		self.local_folder_edit._edited = False
		self.lf_browse_button = QtWidgets.QPushButton("Browse...")
		self.lf_browse_button.clicked.connect(self.on_lf_browse)
		
		lf_container = QtWidgets.QWidget()
		lf_container.setLayout(QtWidgets.QHBoxLayout())
		lf_container.layout().setContentsMargins(0, 0, 0, 0)
		lf_container.layout().addWidget(self.local_folder_edit)
		lf_container.layout().addWidget(self.lf_browse_button)
		
		self.temp_store = Store()
		self.dbrel = self.temp_store.datasources.DBRel()
		servers = []
		logins = []
		names = {}  # {server: [name, ...], ...}
		for row in self.view.menu.get_recent(): # [[url], [identifier, connstr], ...]
			if len(row) == 2:
				server, name = row[1].split("/")[-2:]
				user, server = server.split("@")
				user, password = user.split(":")
				if server not in names:
					names[server] = []
				if name not in names[server]:
					names[server].append(name)
				if server not in servers:
					servers.append(server)
					logins.append([user, password])
		self.server_combo.addItem("")
		for i in range(len(servers)):
			self.server_combo.addItem(servers[i], [servers[i]] + logins[i] + [names[servers[i]]])
		
		self.server_combo.editTextChanged.connect(self.on_server_changed)
		self.name_combo.editTextChanged.connect(self.update)
		
		self.connect_button = QtWidgets.QPushButton(self.parent.connect_caption())
		self.connect_button.clicked.connect(self.on_connect)
		
		self.form.layout().addRow("Server[:port]:", self.server_combo)
		self.form.layout().addRow("Database:", self.name_combo)
		self.form.layout().addRow("Username:", self.user_edit)
		self.form.layout().addRow("Password:", self.pass_edit)
		self.form.layout().addRow("Identifier:", self.identifier_edit)
		self.form.layout().addRow("Local Folder:", lf_container)
		
		self.layout().addWidget(self.form)
		self.layout().addWidget(self.connect_button, alignment = QtCore.Qt.AlignCenter)
		self.layout().addStretch()
		
		self.update()
	
	def get_values(self):
		
		server = self.server_combo.currentText().strip()
		name = self.name_combo.currentText().strip()
		user = self.user_edit.text().strip()
		password = self.pass_edit.text().strip()
		identifier = self.identifier_edit.text().strip()
		local_folder = self.local_folder_edit.text().strip()
		if server and (":" not in server):
			server = "%s:5432" % (server)
		return server, name, user, password, identifier, local_folder
	
	def check_db(self):
		
		self.identifier_edit.blockSignals(True)
		server, name, user, password, identifier, _ = self.get_values()
		connstr = "postgres://%s:%s@%s/%s" % (user, password, server, name)
		if connstr != self._connstr_prev:
			self._valid_db = False
			self._identifier = None
			self.identifier_edit.setText("")
			if "" not in [server, name, user, password]:
				if self.dbrel.set_connstr(connstr):
					self._valid_db = True
					if self.dbrel.is_valid():
						self._identifier = self.dbrel.get_identifier()
						self.identifier_edit.setText(self._identifier)
						self.local_folder_edit._edited = False
		if not self.local_folder_edit._edited:
			local_folder = self.dbrel.get_local_folder()
			self.local_folder_edit.blockSignals(True)
			self.local_folder_edit.setText(local_folder)
			self.local_folder_edit.blockSignals(False)
		self._connstr_prev = connstr
		self.identifier_edit.blockSignals(False)
	
	def update(self, *args):
		
		self.check_db()
		server, name, user, password, identifier, _ = self.get_values()
		is_valid = False
		if as_identifier(identifier, default_base = "http://localhost/deposit") == self._identifier:
			self.connect_button.setText(self.parent.connect_caption())
			is_valid = True
		elif self.parent.creating_enabled() and self._identifier: 
			self.connect_button.setText("Overwrite")
			is_valid = True
		elif self.parent.creating_enabled():
			self.connect_button.setText("Create")
			is_valid = True
		self.connect_button.setEnabled(is_valid and self._valid_db and ("" not in [server, name, user, password, identifier]))
	
	def create_db(self, connstr, identifier, local_folder):
		
		if not self.parent.creating_enabled():
			return False
		ds = self.temp_store.datasources.DBRel(connstr = connstr)
		ds.set_identifier(identifier)
		cursor, _ = ds.connect()
		if cursor:
			return ds.save()
		return False
	
	def on_local_folder_edit(self):
		
		self.local_folder_edit._edited = True
		self.update()
	
	def on_server_changed(self):
		
		data = self.server_combo.currentData()
		server = self.server_combo.currentText().strip()
		if data:
			server, user, password, names = data
			_, curr_name, curr_user, curr_password, _, _ = self.get_values()
			if not (curr_user or curr_password):
				curr_user, curr_password = user, password
				self.user_edit.blockSignals(True)
				self.pass_edit.blockSignals(True)
				self.user_edit.setText(user)
				self.pass_edit.setText(password)
				self.user_edit.blockSignals(False)
				self.pass_edit.blockSignals(False)
			if names:
				self.name_combo.blockSignals(True)
				self.name_combo.clear()
				self.name_combo.addItems(names)
				if curr_name:
					self.name_combo.setCurrentText(curr_name)
				self.name_combo.blockSignals(False)
		self.update()
	
	def on_lf_browse(self):
		
		path = QtWidgets.QFileDialog.getExistingDirectory(self, caption = "Select Local Folder")
		if path:
			self.local_folder_edit.setText(os.path.normpath(os.path.abspath(path)))
			self.local_folder_edit.blockSignals(True)
			self.local_folder_edit.setText(os.path.normpath(os.path.abspath(path)))
			self.local_folder_edit.blockSignals(False)
	
	def on_connect(self):
		
		server, name, user, password, identifier, local_folder = self.get_values()
		if "" in [server, name, user, password, identifier]:
			return
		connstr = "postgres://%s:%s@%s/%s" % (user, password, server, name)
		identifier = as_identifier(identifier, default_base = "http://localhost/deposit")
		if not os.path.isdir(local_folder):
			os.mkdir(local_folder)
		if identifier == self._identifier:
			if self.temp_store.get_datasource(identifier, connstr):
				self.parent.on_connect(identifier, connstr, local_folder, created = False)
			else:
				QtWidgets.QMessageBox.critical(self, "Error", "Could not connect to database.")
		else:
			if self.create_db(connstr, identifier, local_folder):
				self.parent.on_connect(identifier, connstr, local_folder, created = True)
			else:
				QtWidgets.QMessageBox.critical(self, "Error", "Could not create database.")

