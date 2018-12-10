from deposit import Broadcasts
from deposit.commander.CmdDict import (CmdDict)
from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.toolbar._ordering import (ordering)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class Toolbar(CmdDict, ViewChild):

	def __init__(self, model, view):

		self.toolbar = None
		self.actions = {} # {name: QAction, ...}

		CmdDict.__init__(self)
		ViewChild.__init__(self, model, view)

		self.set_up()

	def set_up(self):

		self.toolbar = self.view.addToolBar("Main")
		self.toolbar.setIconSize(QtCore.QSize(36,36))
		for i, row in enumerate(ordering):
			for name in row:
				if name in self.classes:
					self[name] = self.classes[name](self.model, self.view)
					if not self[name].combo() is None:
						label = None
						if self[name].name():
							label = QtWidgets.QLabel(self[name].name() + ": ", self.view)
						self.actions[name] = QtWidgets.QComboBox(self.view)
						self.actions[name].setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
						self.actions[name].setEditable(True)
						self.actions[name].currentTextChanged.connect(self.on_combo_text_changed)
						if label:
							self.toolbar.addWidget(label)
						self.toolbar.addWidget(self.actions[name])
					else:
						self.actions[name] = QtWidgets.QAction(self[name].name(), self.view)
						self.actions[name].setData(name)
						self.toolbar.addAction(self.actions[name])
						self.actions[name].hovered.connect(self.on_action_hovered)
			if i < len(ordering) - 1:
				self.toolbar.addSeparator()

		self.toolbar.actionTriggered.connect(self.on_triggered)
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_view_action)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)

		self.update_tools()
	
	def update_tools(self, clear_text = False):

		for name in self:
			if not self[name].combo() is None:
				self.stop_broadcasts()
				text = self.actions[name].currentText()
				self.actions[name].blockSignals(True)
				self.actions[name].clear()
				self.actions[name].addItems(self[name].combo())
				i = self.actions[name].findText(text, flags = QtCore.Qt.MatchExactly|QtCore.Qt.MatchCaseSensitive)
				if i > -1:
					self.actions[name].setCurrentIndex(i)
				elif (text and not clear_text):
					self.actions[name].setCurrentText(text)
				self.actions[name].adjustSize()
				self.actions[name].blockSignals(False)
				self.resume_broadcasts()
				continue
			self.actions[name].setText(self[name].name())
			icon = self[name].icon()
			if icon:
				icon = self.view.get_icon(icon)
				self.actions[name].setIcon(icon)
			shortcut = self[name].shortcut()
			if shortcut:
				self.actions[name].setShortcut(QtGui.QKeySequence(shortcut))
			self.actions[name].setCheckable(self[name].checkable())
			self.actions[name].setToolTip(self[name].help())
			self.actions[name].setChecked(self[name].checked())
			self.actions[name].setEnabled(self[name].enabled())
	
	def get_combo_value(self, name):

		if (name in self.actions) and isinstance(self.actions[name], QtWidgets.QComboBox):
			return self.actions[name].currentText()

	def set_combo_value(self, name, text):

		if (name in self.actions) and isinstance(self.actions[name], QtWidgets.QComboBox):

			self.actions[name].setCurrentText(text)

	def on_triggered(self, action):

		self[str(action.data())].triggered(action.isChecked())
		self.update_tools()

	def on_combo_text_changed(self, text):

		self.broadcast(Broadcasts.VIEW_ACTION)

	def on_action_hovered(self):

		self.view.statusbar.message(self.view.sender().toolTip())

	def on_view_action(self, args):

		self.update_tools()

	def on_store_changed(self, args):

		self.update_tools()

	def on_saved(self, *args):

		self.update_tools()

	def on_loaded(self, args):

		self.update_tools(clear_text = True)
