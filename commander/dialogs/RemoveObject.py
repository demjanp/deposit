from deposit.commander.dialogs._Dialog import (Dialog)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class RemoveObject(Dialog):

	def title(self):

		if len(self.objects) > 1:
			return "Remove Objects"
		else:
			return "Remove Object"

	def set_up(self, objects):

		self.objects = objects

		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)

		label = QtWidgets.QLabel("Remove the selected object%s?" % ("s" if (len(self.objects) > 1) else ""), self)

		self.layout.addWidget(label)

	def process(self):

		ids = set([obj.id for obj in self.objects])
		for id in ids:
			del self.model.objects[id]

