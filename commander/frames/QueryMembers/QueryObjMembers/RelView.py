from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryLst import (QueryLst)
from deposit.commander.frames.QueryMembers.QuerySelection import (QuerySelection)
from natsort import (natsorted)

from PySide2 import (QtWidgets, QtCore, QtGui)

class HeaderButton(QtWidgets.QToolButton):
	
	def __init__(self, parent, label, idx):
		
		self.parent = parent
		self.idx = idx
		
		QtWidgets.QToolButton.__init__(self, parent)
		
		self.setText(label)
		self.setArrowType(QtCore.Qt.DownArrow)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.setAutoRaise(True)
		self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
		
		self.clicked.connect(self.on_header_clicked)
	
	def on_header_clicked(self, *args):
		
		self.parent.on_header_clicked(self)

class QueryButton(QtWidgets.QToolButton):
	
	def __init__(self, parent, idx):
		
		self.parent = parent
		self.idx = idx
		
		QtWidgets.QToolButton.__init__(self, parent)
		
		self.setText("Query")
		self.setArrowType(QtCore.Qt.RightArrow)
		self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		self.setAutoRaise(True)
		self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.setStyleSheet("QToolButton {font: bold; border-top: 1px solid white; border-left: 1px solid white; border-bottom: 1px solid gray; border-right: 1px solid gray;} QToolButton:pressed {border-top: 1px solid gray; border-left: 1px solid gray; border-bottom: 1px solid white; border-right: 1px solid white;}")
		
		self.clicked.connect(self.on_query_clicked)
	
	def on_query_clicked(self, *args):
		
		self.parent.on_query_clicked(self.idx)

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
		
		# collect all combinations of relation and class / classless for query
		self.relations = [] # [[rel, cls], ...]
		found = set([])
		for cls1 in self.query.classes:
			for rel in self.model.classes[cls1].relations:
				for cls2 in self.model.classes[cls1].relations[rel]:
					found.add((rel, cls2))
				found.add((rel, "!*"))
		for rel, cls in found:
			self.relations.append([rel, cls])
			self.visible_widgets["%s_%s" % (rel, cls)] = True
		
		# sort relations by class order
		self.relations = natsorted(self.relations, key = lambda row: [row[0], -1] if (row[1] == "!*") else [row[0], self.model.classes[row[1]].order])
		
		self.clear_layout(self.layout)
		
		for i in range(len(self.relations)):
			rel, cls = self.relations[i]
			label = ".%s.%s" % (rel, cls)
			
			header = HeaderButton(self, label, i)
			button_query = QueryButton(self, i)
			
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
			key = "%s_%s" % (rel, cls)
			visible = (key in self.visible_widgets) and self.visible_widgets[key]
			found = False
			if rel in obj.relations:
				cls0 = list(obj.classes.keys())
				if len(cls0) == 0:
					cls0 = "!*"
				else:
					cls0 = cls0[0]
				if cls0 == cls:
					querystr = "SELECT %s.* WHERE id(%s) in {%s}" % (cls, cls, ",".join([str(obj_id) for obj_id in obj.relations[rel].keys()]))
				else:
					querystr = "SELECT %s.* WHERE id(%s) == %d" % (cls, cls0, obj.id)
				query = self.model.query(querystr)
				if len(query):
					found = True
					self.tables.append(QueryLst(self.model, self.view, self.parent, query, obj.relations[rel]))
					table_layout.addWidget(self.tables[-1])
					table_widget.setVisible(visible)
					header_widget.setEnabled(True)
			if not found:
				header_widget.setEnabled(False)
	
	def get_selected(self):
		
		selected = None
		for table in self.tables:
			if selected is None:
				selected = table.get_selected()
			else:
				selected.update(table.get_selected().indexes)
		if selected is None:
			return QuerySelection(self.model, self.view)
		return selected
	
	def get_objects(self):
		
		objects = []
		for table in self.tables:
			objects += table.get_objects()
		return objects
	
	def on_header_clicked(self, header):
		
		idx = header.idx
		table_widget = self.layout.itemAt(idx * 2 + 1).widget()
		if table_widget.layout().count():
			key = "%s_%s" % tuple(self.relations[idx])
			self.visible_widgets[key] = not self.visible_widgets[key]
			table_widget.setVisible(self.visible_widgets[key])
			if self.visible_widgets[key]:
				header.setArrowType(QtCore.Qt.DownArrow)
			else:
				header.setArrowType(QtCore.Qt.RightArrow)
	
	def on_query_clicked(self, idx):
		
		table_widget = self.layout.itemAt(idx * 2 + 1).widget()
		if table_widget.layout().count():
			self.parent.on_query_activated(table_widget.layout().itemAt(0).widget().query.querystr)

