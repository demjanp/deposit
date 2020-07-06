from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_identifier)

from PySide2 import (QtWidgets, QtCore, QtGui)

class OpenDBRel(DModule, QtWidgets.QFrame):
	
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
		
		self.dbrel = self.model.datasources.DBRel()
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
		
		self.connect_button = QtWidgets.QPushButton("Connect")
		self.connect_button.clicked.connect(self.on_connect)
		
		self.form.layout().addRow("Server[:port]:", self.server_combo)
		self.form.layout().addRow("Database:", self.name_combo)
		self.form.layout().addRow("Username:", self.user_edit)
		self.form.layout().addRow("Password:", self.pass_edit)
		self.form.layout().addRow("Identifier:", self.identifier_edit)
		
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
		if server and (":" not in server):
			server = "%s:5432" % (server)
		return server, name, user, password, identifier
	
	def check_db(self):
		
		self.identifier_edit.blockSignals(True)
		server, name, user, password, identifier = self.get_values()
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
		self._connstr_prev = connstr
		self.identifier_edit.blockSignals(False)
	
	def update(self, *args):
		
		self.check_db()
		server, name, user, password, identifier = self.get_values()
		if as_identifier(identifier) == self._identifier:
			self.connect_button.setText("Connect")
		elif self._identifier: 
			self.connect_button.setText("Overwrite")
		else:
			self.connect_button.setText("Create")
		self.connect_button.setEnabled(self._valid_db and ("" not in [server, name, user, password, identifier]))
	
	def create_db(self, connstr, identifier):
		
		self.dbrel.set_connstr(connstr)
		self.dbrel.set_identifier(identifier)
		cursor, _ = self.dbrel.connect()
		if cursor:
			self.model.set_datasource(self.dbrel)
			return self.dbrel.save()
		return False
	
	def on_server_changed(self):
		
		data = self.server_combo.currentData()
		server = self.server_combo.currentText().strip()
		if data:
			server, user, password, names = data
			_, curr_name, curr_user, curr_password, _ = self.get_values()
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
	
	def on_connect(self):
		
		server, name, user, password, identifier = self.get_values()
		if "" in [server, name, user, password, identifier]:
			return
		connstr = "postgres://%s:%s@%s/%s" % (user, password, server, name)
		identifier = as_identifier(identifier)
		if identifier == self._identifier:
			self.model.load(identifier, connstr)
			self.parent.close()
		else:
			reply = QtWidgets.QMessageBox.question(self, "Overwrite Data?", "All existing data in database %s will be lost. Proceed?" % (name), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
			if reply != QtWidgets.QMessageBox.Yes:
				return
			if self.create_db(connstr, identifier):
				self.parent.close()
			else:
				QtWidgets.QMessageBox.critical(self, "Error", "Could not create database.")

