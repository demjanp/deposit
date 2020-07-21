from deposit import Broadcasts
from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Import(Dialog):
	
	def title(self):
		
		return "Import External Data"
	
	def set_up(self, external_frame):
		
		self.external_frame = external_frame
		
		self.setMinimumWidth(360)
		self.setModal(True)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		targets = self.external_frame.get_targets()  # {column_idx: target, ...}
		rows = [targets[idx] for idx in sorted(targets.keys())]
		self.layout().addWidget(QtWidgets.QLabel("<b>Descriptors:</b><p>%s</p>" % ("<br/>".join(rows))))
		
		self.layout().addWidget(QtWidgets.QLabel("<b>Relations:</b>"))
		self.relations = QtWidgets.QPlainTextEdit()
		
		self.layout().addWidget(self.relations)
	
	def process(self):
		
		relations = []
		for row in self.relations.toPlainText().strip().split("\n"):
			row = [val.strip() for val in row.split(".")]
			if len(row) != 3:
				continue
			relations.append(row)
		self.external_frame.import_data(relations)
