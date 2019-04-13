from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryLst import (QueryLst)
from natsort import (natsorted)

from PySide2 import (QtWidgets, QtCore, QtGui)

class RelView(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query, visible_widgets = {}):
		
		self.query = query
		self.tables = [] # [QueryLst, ...]
		self.relations = [] # [[relation_name, class_name], ...]
		self.visible_widgets = visible_widgets # {rel_cls: True/False, ...}
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.populate_headers()
	
	def populate_headers(self):
		
		# collect all combinations of reltion and class / classless for query
		self.relations = [] # [[rel, cls], ...]
		for row in self.query:
			obj = row.object
			for rel in obj.relations:
				for id2 in obj.relations[rel]:
					if len(obj.relations[rel][id2].classes) == 0:
						if not [rel, "!*"] in self.relations:
							self.relations.append([rel, "!*"])
					for cls in obj.relations[rel][id2].classes:
						if not [rel, cls] in self.relations:
							self.relations.append([rel, cls])
							key = "%s_%s" % (rel, cls)
							if not key in self.visible_widgets:
								self.visible_widgets[key] = True
		
		# sort relations by class order
		self.relations = natsorted(self.relations, key = lambda row: -1 if (row[1] == "!*") else self.model.classes[row[1]].order)
		
		self.clear_layout(self.layout)
		
		for i in range(len(self.relations)):
			rel, cls = self.relations[i]
			label = ".%s.%s" % (rel, cls)
			
			header = QtWidgets.QToolButton()
			header.setText(label)
			header.setArrowType(QtCore.Qt.DownArrow)
			header.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
			header.setAutoRaise(True)
			header.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
			header.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
			header.clicked.connect(self.on_header_clicked)
			header.idx = i
			
			button_query = QtWidgets.QToolButton()
			button_query.setText("Query")
			button_query.setArrowType(QtCore.Qt.RightArrow)
			button_query.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
			button_query.setAutoRaise(True)
			button_query.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
			button_query.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
			button_query.clicked.connect(self.on_query_clicked)
			button_query.idx = i
			
			header_layout = QtWidgets.QHBoxLayout()
			header_layout.setContentsMargins(0, 0, 0, 0)
			header_layout.addWidget(header)
			header_layout.addWidget(button_query)
			
			header_widget = QtWidgets.QWidget()
			header_widget.setLayout(header_layout)
			
			table_widget = QtWidgets.QWidget(self)
			table_layout = QtWidgets.QVBoxLayout()
			table_layout.setContentsMargins(0, 0, 0, 0)
			table_widget.setLayout(table_layout)
			
			self.layout.addWidget(header_widget)
			self.layout.addWidget(table_widget)
	
	def populate_data(self, obj):

		self.tables = []
		for i in range(len(self.relations)):
			table_widget = self.layout.itemAt(i * 2 + 1).widget()
			table_layout = table_widget.layout()
			if table_layout.count():
				table_layout.removeItem(table_layout.itemAt(0))
			
			header_widget = self.layout.itemAt(i * 2).widget()

			rel, cls = self.relations[i]
			visible = self.visible_widgets["%s_%s" % (rel, cls)]
			found = False
			if rel in obj.relations:
				cls0 = list(obj.classes.keys())
				if len(cls0) == 0:
					cls0 = "!*"
				else:
					cls0 = cls0[0]
				querystr = "SELECT %s.* WHERE id(%s) == %d" % (cls, cls0, obj.id)
				query = self.model.query(querystr)
				if len(query):
					found = True
					self.tables.append(QueryLst(self.model, self.view, table_widget, query, obj.relations[rel]))
					table_layout.addWidget(self.tables[-1])
					table_widget.setVisible(visible)
					header_widget.setEnabled(True)
			if not found:
				header_widget.setEnabled(False)
	
	def get_selected(self):
		
		selected = []
		for table in self.tables:
			selected += table.get_selected()
		return selected
	
	def on_header_clicked(self):
		
		sender = self.sender()
		idx = sender.idx
		table_widget = self.layout.itemAt(idx * 2 + 1).widget()
		if table_widget.layout().count():
			key = "%s_%s" % tuple(self.relations[idx])
			self.visible_widgets[key] = not self.visible_widgets[key]
			table_widget.setVisible(self.visible_widgets[key])
			if self.visible_widgets[key]:
				sender.setArrowType(QtCore.Qt.DownArrow)
			else:
				sender.setArrowType(QtCore.Qt.RightArrow)
	
	def on_query_clicked(self):
		
		sender = self.sender()
		idx = sender.idx
		table_widget = self.layout.itemAt(idx * 2 + 1).widget()
		if table_widget.layout().count():
			self.view.mdiarea.create("Query", table_widget.layout().itemAt(0).widget().query.querystr)

