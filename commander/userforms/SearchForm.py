from deposit import Broadcasts
from deposit.commander.userforms._Form import (Form)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class SearchForm(Form):
	
	def set_up(self, elements):
		
		# self.controls = {class.descriptor: QWidget, group_frame_nr: {class.descriptor: QWidget, ...}, ...}
		
		self.central_frame.setLayout(QtWidgets.QVBoxLayout())
		self.central_frame.layout().setContentsMargins(0, 0, 0, 0)
		self.form_frame = QtWidgets.QFrame()
		self.form_frame.setLayout(QtWidgets.QFormLayout())
		self.form_frame.layout().setContentsMargins(10, 10, 10, 10)
		self.central_frame.layout().addWidget(self.form_frame)
		
		for element in elements[2:]:  # [tag, ...]; tag = [control type, class.descriptor, label]
			
			label, ctrl, select = self.make_row(element)
			if label is None:
				continue
			self.controls[select] = ctrl
			if isinstance(ctrl, QtWidgets.QComboBox):
				self.update_combo(select)
			self.form_frame.layout().addRow(label, self.controls[select])
		
		self.layout().addStretch()
	
	def on_submit(self, *args):
		
		query = "SELECT %s" % (", ".join(self.controls.keys()))
		conditions = []
		for select in self.controls:
			value = self.get_value(select)
			if value:
				conditions.append("(%s == '%s')" % (select, value))
		if conditions:
			query += " WHERE %s" % (" and ".join(conditions))
		self.view.mdiarea.create("Query", query)
	
	def on_reset(self, *args):
		
		for select in self.controls:
			self.set_control(select, None)

