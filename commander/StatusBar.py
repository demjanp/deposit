from deposit.commander.ViewChild import (ViewChild)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class StatusBar(ViewChild, QtWidgets.QStatusBar):

	def __init__(self, model, view):

		ViewChild.__init__(self, model, view)
		QtWidgets.QStatusBar.__init__(self, view)

		self.set_up()

	def set_up(self):

		pass

	def message(self, text):

		self.showMessage(text)
