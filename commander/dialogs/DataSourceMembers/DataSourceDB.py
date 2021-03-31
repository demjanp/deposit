from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_identifier)
from deposit.store.Store import (Store)

import os
from natsort import natsorted
from collections import defaultdict
from PySide2 import (QtWidgets, QtCore, QtGui)

class DataSourceDB(DModule, QtWidgets.QFrame):
	
	def __init__(self, model, view, parent):
		
		self.model = model
		self.view = view
		self.parent = parent
		
		self._connstr_prev = None
		self._schemas = defaultdict(lambda: defaultdict(list))  # {server: {db_name: [schema, ...], ...}, ...}
		self._identifiers = []
		
		DModule.__init__(self)
		QtWidgets.QFrame.__init__(self, parent)
		
		self.form = QtWidgets.QWidget()
		self.form.setLayout(QtWidgets.QFormLayout())
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.server_combo = QtWidgets.QComboBox()
		self.server_combo.setEditable(True)
		self.db_name_combo = QtWidgets.QComboBox()
		self.db_name_combo.setEditable(True)
		self.schema_name_combo = QtWidgets.QComboBox()
		self.schema_name_combo.setEditable(True)
		self.schema_name_combo.setCurrentText("public")
		self.user_edit = QtWidgets.QLineEdit("")
		self.user_edit.textChanged.connect(self.update)
		self.pass_edit = QtWidgets.QLineEdit("")
		self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
		self.pass_edit.textChanged.connect(self.update)
		self.identifier_combo = QtWidgets.QComboBox()
		self.identifier_combo.setEditable(True)
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
		self.db = self.temp_store.datasources.DB()
		servers = []
		logins = []
		names = {}  # {server: [name, ...], ...}
		for row in self.view.menu.get_recent(): # [[url], [identifier, connstr], ...]
			if len(row) == 2:
				server, name = row[1].split("/")[-2:]
				schema = "public"
				if "?" in name:
					name, schema = name.split("?")
					schema = schema.split("%3D")[-1]
				user, server = server.split("@")
				user, password = user.split(":")
				if server not in names:
					names[server] = []
				if name not in names[server]:
					names[server].append(name)
				if schema not in self._schemas[server][name]:
					self._schemas[server][name].append(schema)
				if server not in servers:
					servers.append(server)
					logins.append([user, password])
		self.server_combo.addItem("")
		for i in range(len(servers)):
			self.server_combo.addItem(servers[i], [servers[i]] + logins[i] + [names[servers[i]]])
		
		self.server_combo.editTextChanged.connect(self.on_server_changed)
		self.db_name_combo.editTextChanged.connect(self.update)
		self.schema_name_combo.editTextChanged.connect(self.update)
		self.identifier_combo.editTextChanged.connect(self.on_identifier_changed)
		
		self.connect_button = QtWidgets.QPushButton(self.parent.connect_caption())
		self.connect_button.clicked.connect(self.on_connect)
		
		self.form.layout().addRow("Server[:port]:", self.server_combo)
		self.form.layout().addRow("Database:", self.db_name_combo)
		self.form.layout().addRow("Schema:", self.schema_name_combo)
		self.form.layout().addRow("Username:", self.user_edit)
		self.form.layout().addRow("Password:", self.pass_edit)
		self.form.layout().addRow("Identifier:", self.identifier_combo)
		self.form.layout().addRow("Local Folder:", lf_container)
		
		self.layout().addWidget(self.form)
		self.layout().addWidget(self.connect_button, alignment = QtCore.Qt.AlignCenter)
		self.layout().addStretch()
		
		self.update()
	
	def get_values(self):
		
		server = self.server_combo.currentText().strip()
		name = self.db_name_combo.currentText().strip()
		schema = self.schema_name_combo.currentText().strip()
		user = self.user_edit.text().strip()
		password = self.pass_edit.text().strip()
		identifier = self.identifier_combo.currentText().strip()
		local_folder = self.local_folder_edit.text().strip()
		if server and (":" not in server):
			server = "%s:5432" % (server)
		return server, name, schema, user, password, identifier, local_folder
	
	def load_schemas(self):
		
		server, name, curr_schema, user, password, identifier, _ = self.get_values()
		if not self._schemas[server][name]:
			connstr = "postgres://%s:%s@%s/%s" % (user, password, server, name)
			conn = None
			try:
				conn = psycopg2.connect(connstr)
			except:
				pass
			if conn is not None:
				cursor = conn.cursor()
				cursor.execute("SELECT schema_name FROM information_schema.schemata")
				self._schemas[server][name] = natsorted([row[0] for row in cursor.fetchall()])
		if "public" not in self._schemas[server][name]:
			self._schemas[server][name].append("public")
		self.schema_name_combo.blockSignals(True)
		self.schema_name_combo.clear()
		self.schema_name_combo.addItems(self._schemas[server][name])
		if curr_schema:
			self.schema_name_combo.setCurrentText(curr_schema)
		self.schema_name_combo.blockSignals(False)
	
	def load_identifiers(self):
		
		self.identifier_combo.blockSignals(True)
		server, name, schema, user, password, identifier, _ = self.get_values()
		do_not_load = (self._schemas[server][name] and (schema not in self._schemas[server][name]))
		connstr = "postgres://%s:%s@%s/%s?options=-csearch_path%%3D%s" % (user, password, server, name, schema)
		if connstr != self._connstr_prev:
			self._identifiers = []
			self.identifier_combo.clear()
			if (not do_not_load) and ("" not in [server, name, schema, user, password]):
				if self.db.set_connstr(connstr):
					self._identifiers = self.db.get_identifiers()
					if self._identifiers:
						self.identifier_combo.addItems(self._identifiers)
						self.local_folder_edit._edited = False
		if identifier:
			self.identifier_combo.setCurrentText(identifier)
		if (not identifier) and self._identifiers:
			identifier = self._identifiers[0]
		if (not self.local_folder_edit._edited) and (identifier in self._identifiers):
			local_folder = self.db.get_local_folder(identifier)
			self.local_folder_edit.blockSignals(True)
			self.local_folder_edit.setText(local_folder)
			self.local_folder_edit.blockSignals(False)
		self._connstr_prev = connstr
		self.identifier_combo.blockSignals(False)
	
	def update(self, *args):
		
		self.load_schemas()
		self.load_identifiers()
		server, name, schema, user, password, identifier, local_folder = self.get_values()
		is_valid = False
		if as_identifier(identifier, default_base = "http://localhost/deposit") in self._identifiers:
			self.connect_button.setText(self.parent.connect_caption())
			is_valid = True
		elif self.parent.creating_enabled():
			self.connect_button.setText("Create")
			is_valid = True
		if not local_folder:
			is_valid = False
		self.connect_button.setEnabled(is_valid and ("" not in [server, name, user, password, identifier, local_folder]))
	
	def create_db(self, connstr, identifier):
		
		if not self.parent.creating_enabled():
			return False
		ds = self.temp_store.datasources.DB(identifier = identifier, connstr = connstr)
		cursor, _ = ds.connect(create_schema = True)
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
			_, curr_name, curr_schema, curr_user, curr_password, _, _ = self.get_values()
			if not (curr_user or curr_password):
				curr_user, curr_password = user, password
				self.user_edit.blockSignals(True)
				self.pass_edit.blockSignals(True)
				self.user_edit.setText(user)
				self.pass_edit.setText(password)
				self.user_edit.blockSignals(False)
				self.pass_edit.blockSignals(False)
			if names:
				self.db_name_combo.blockSignals(True)
				self.db_name_combo.clear()
				self.db_name_combo.addItems(names)
				if curr_name:
					self.db_name_combo.setCurrentText(curr_name)
				self.db_name_combo.blockSignals(False)
		self.update()
	
	def on_identifier_changed(self):
		
		self.local_folder_edit._edited = False
		self.update()
	
	def on_lf_browse(self):
		
		path = QtWidgets.QFileDialog.getExistingDirectory(self, caption = "Select Local Folder")
		if path:
			self.local_folder_edit._edited = True
			self.local_folder_edit.setText(os.path.normpath(os.path.abspath(path)))
	
	def on_connect(self):
		
		server, name, schema, user, password, identifier, local_folder = self.get_values()
		if "" in [server, name, schema, user, password, identifier]:
			return
		connstr = "postgres://%s:%s@%s/%s?options=-csearch_path%%3D%s" % (user, password, server, name, schema)
		identifier = as_identifier(identifier, default_base = "http://localhost/deposit")
		if not os.path.isdir(local_folder):
			os.mkdir(local_folder)
		if identifier in self._identifiers:
			if self.temp_store.get_datasource(identifier, connstr):
				self.parent.on_connect(identifier, connstr, local_folder, created = False)
			else:
				QtWidgets.QMessageBox.critical(self, "Error", "Could not connect to database.")
		else:
			if self.create_db(connstr, identifier):
				self.parent.on_connect(identifier, connstr, local_folder, created = True)
			else:
				QtWidgets.QMessageBox.critical(self, "Error", "Could not create database.")

