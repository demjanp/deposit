from deposit.DModule import (DModule)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Dialog(DModule, QtWidgets.QDialog):

	def __init__(self, model, view, *args):
		
		self.model = model
		self.view = view
		self._closed = False
		self.buttonBox = None

		DModule.__init__(self)
		QtWidgets.QDialog.__init__(self, self.view)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		
		self.finished.connect(self.on_finished)
		
		self.set_up(*args)
		
		self.setWindowTitle(self.title())

		ok, cancel = self.button_box()
		if ok or cancel:
			if ok and cancel:
				flags = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
			elif ok:
				flags = QtWidgets.QDialogButtonBox.Ok
			else:
				flags = QtWidgets.QDialogButtonBox.Cancel
			self.buttonBox = QtWidgets.QDialogButtonBox(flags, QtCore.Qt.Horizontal)
			self.buttonBox.accepted.connect(self.accept)
			self.buttonBox.rejected.connect(self.reject)
			QtWidgets.QDialog.layout(self).addWidget(self.buttonBox)
		
		self.adjustSize()

	def set_enabled(self, state):

		if self.buttonBox is not None:
			self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(state)

	def set_closed(self):
		
		self.disconnect_broadcast()
		self._closed = True
	
	def closed(self):
		
		visible = False
		try:
			visible = self.isVisible()
		except:
			pass
		if not visible:
			return True
		return self._closed
	
	def on_finished(self, code):
		
		self.view.dialogs.on_finished(code, self)
	
	def set_up(self, *args):
		# re-implement
		
		pass
	
	def title(self):
		
		return self.__class__.__name__
	
	def button_box(self):
		# return True/False for Ok, Cancel buttons
		
		return True, True
	
	def process(self):
		
		pass
	
	def cancel(self):
		# re-implement
		
		pass
