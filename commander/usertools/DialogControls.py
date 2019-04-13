from PySide2 import (QtWidgets, QtCore, QtGui)

class DialogControl(object):
	
	def __init__(self, model, user_control):
		
		self.model = model
		self.user_control = user_control
	
	def set_object(self, id):
		
		value = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
		if value is None:
			value = ""
		self.set_value(value)
	
	def set_value(self, value):
		
		return None
	
	def get_value(self):
		
		return None
	
class LineEdit(DialogControl, QtWidgets.QLineEdit):
	
	def __init__(self, model, user_control):
		
		self.last_added = ""
		self.values = []
		self._autocompleting = True
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QLineEdit.__init__(self)
		
		self.values = set()
		for id in self.model.classes[self.user_control.dclass].objects:
			val = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
			if val is not None:
				self.values.add(val)
		self.values = sorted(list(self.values))
		
		self.textChanged.connect(self.on_text_changed)
	
	def set_value(self, value):
		
		if value is None:
			value = ""
		value = str(value)
		self.blockSignals(True)
		self.setText(value)
		self.blockSignals(False)
		if value == "":
			self._autocompleting = True
		else:
			self._autocompleting = False
	
	def get_value(self):
		
		return self.text().strip()

	def on_text_changed(self, *args):
		
		text = self.text()
		if not text:
			self.last_added = ""
			self._autocompleting = True
			return
		if self._autocompleting:
			for value in self.values:
				if value.lower().startswith(text.lower()):
					if value[len(text):] == self.last_added:
						self.last_added = ""
						return
					self.blockSignals(True)
					self.setText(value)
					self.setSelection(len(text), len(value))
					self.last_added = value[len(text):]
					self.blockSignals(False)
					return
		self.last_added = ""

class PlainTextEdit(DialogControl, QtWidgets.QPlainTextEdit):
	
	def __init__(self, model, user_control):
		
		self.last_added = ""
		self.values = []
		self._autocompleting = True
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QPlainTextEdit.__init__(self)
		
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		
		self.values = set()
		for id in self.model.classes[self.user_control.dclass].objects:
			val = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
			if val is not None:
				self.values.add(val)
		self.values = sorted(list(self.values))
		
		self.textChanged.connect(self.on_text_changed)
	
	def set_value(self, value):
		
		if value is None:
			value = ""
		value = str(value)
		self.blockSignals(True)
		self.setPlainText(value)
		self.blockSignals(False)
		if value == "":
			self._autocompleting = True
		else:
			self._autocompleting = False
		
	def get_value(self):
		
		return self.toPlainText().strip()
	
	def autocomplete(self):
		
		text = self.toPlainText()
		if not text:
			self.last_added = ""
			self._autocompleting = True
			return
		if self._autocompleting:
			for value in self.values:
				if value.lower().startswith(text.lower()):
					if value[len(text):] == self.last_added:
						self.last_added = ""
						return
					self.blockSignals(True)
					self.setPlainText(value)
					cursor = self.textCursor()
					cursor.setPosition(len(text))
					cursor.setPosition(len(value), QtGui.QTextCursor.KeepAnchor)
					self.setTextCursor(cursor)
					self.last_added = cursor.selectedText()
					self.blockSignals(False)
					return
		self.last_added = ""
	
	def set_num_rows(self, rows):
		
		doc = self.document()
		line = QtGui.QFontMetrics(doc.defaultFont()).lineSpacing()
		margins = self.contentsMargins()
		h = line * rows + (doc.documentMargin() + self.frameWidth()) * 2 + margins.top() + margins.bottom()
		if self.height() != h:
			self.setFixedHeight(h)
	
	def resize_to_fit(self):
		
		rows = max(2, self.document().size().height() + 1)
		self.set_num_rows(rows)
	
	def on_text_changed(self, *args):
		
		self.autocomplete()
		self.resize_to_fit()
	
	def resizeEvent(self, event):
		
		QtWidgets.QPlainTextEdit.resizeEvent(self, event)
		self.resize_to_fit()

class ComboBox(DialogControl, QtWidgets.QComboBox):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QComboBox.__init__(self)
		self.setEditable(True)
		
		self.set_value(None)
	
	def set_value(self, value):
		
		values = set()
		for id in self.model.classes[self.user_control.dclass].objects:
			val = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
			if val is not None:
				values.add(val)
		values = sorted(list(values))
		self.clear()
		if values:
			self.addItems([""] + values)
		if value is not None:
			value = str(value)
			if value in values:
				self.setCurrentIndex(values.index(value) + 1)
			elif values:
				self.setItemText(0, value)
			else:
				self.setCurrentText(value)
		
	def get_value(self):
		
		return self.currentText().strip()
	
	def wheelEvent(self, event):
		
		pass

class CheckBox(DialogControl, QtWidgets.QCheckBox):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QCheckBox.__init__(self)
	
	def set_value(self, value):
		
		try:
			value = bool(int(value))
		except:
			value = False
		self.setChecked(value)
	
	def get_value(self):
		
		return str(int(self.isChecked()))

