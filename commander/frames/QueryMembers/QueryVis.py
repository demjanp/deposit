from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.GraphVisView import (GraphVisView)
from deposit.commander.frames.QueryMembers.QueryItem import (DModelIndex)
from deposit.commander.frames.QueryMembers.QuerySelection import (QuerySelection)

from PySide2 import (QtWidgets, QtCore, QtGui)
from networkx.drawing.nx_agraph import graphviz_layout
from pathlib import Path
import networkx as nx
import os

class QueryVisLazy(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		
		self._row_count = 0
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up()
	
	def set_up(self):
		
		self._row_count = len(self.query)
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def get_row_count(self):
		
		return self._row_count

class QueryVis(Frame, QtWidgets.QMainWindow):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		
		self._row_count = 0
		self._selection = None
		
		self._nodes = {}  # {node_id: label, ...}
		self._edges = []  # [[source_id, target_id, label], ...]
		self._attributes = {}  # {node_id: [(name, value), ...], ...}
		self._positions = {}  # {node_id: (x, y), ...}
		
		self._actions = {} # {name: QAction, ...}
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QMainWindow.__init__(self)
		
		self._selection = QuerySelection(self.model, self.view, [])
		
		central_widget = QtWidgets.QWidget(self)
		central_widget.setLayout(QtWidgets.QVBoxLayout())
		central_widget.layout().setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(central_widget)
		
		self.set_up_toolbar()
		
		self.graph_view = GraphVisView()
		self.graph_view.activated.connect(self.on_activated)
		self.graph_view.selected.connect(self.on_selected)
		central_widget.layout().addWidget(self.graph_view)
		
		self.set_up()
		self.graph_view.reset_scene()
	
	def set_up(self):
		
		self.populate()
	
	def set_up_toolbar(self):
		
		self.toolbar = self.addToolBar("Graph")
		actions = [
			["node_view", "Show Nodes", "nodes.svg"],
			["value_view", "Show Values", "attributes_simple.svg"],
			["descriptor_view", "Show Descriptors with Values", "attributes.svg"],
			["reset_layout", "Re-arrange Layout", "geometry.svg"],
			["#separator", None, None],
			["zoom_in", "Zoom In", "zoom_in.svg"],
			["zoom_out", "Zoom Out", "zoom_out.svg"],
			["zoom_reset", "Zoom Reset", "zoom_reset.svg"],
			["#separator", None, None],
			["save_pdf", "Save As PDF", "save_pdf.svg"],
		]
		
		for name, text, icon in actions:
			if name == "#separator":
				self.toolbar.addSeparator()
			else:
				self._actions[name] = QtWidgets.QAction(self.view.get_icon(icon), text, self)
				self._actions[name].setData(name)
				self.toolbar.addAction(self._actions[name])
		
		self._actions["node_view"].setCheckable(True)
		self._actions["value_view"].setCheckable(True)
		self._actions["descriptor_view"].setCheckable(True)
		self._actions["node_view"].setChecked(False)
		self._actions["value_view"].setChecked(True)
		self._actions["descriptor_view"].setChecked(False)
		
		self.toolbar.actionTriggered.connect(self.on_tool_triggered)
	
	def populate(self, reset_positions = False, max_nodes = 1000, max_edges = 3000):
		
		self._nodes.clear()
		self._edges.clear()
		self._attributes.clear()
		self._positions.clear()
		
		G = nx.MultiDiGraph()
		if len(self.query) <= max_nodes:
			ids_found = set([])
			for row in self.query:
				obj_id = row.object.id
				ids_found.add(obj_id)
				self._nodes[obj_id] = str(obj_id)
				G.add_node(obj_id)
				self._attributes[obj_id] = []
				for column in row:
					descriptor = row[column].descriptor
					if descriptor is None:
						continue
					if descriptor.label.__class__.__name__ != "DString":
						continue
					if descriptor.label.value:
						self._attributes[obj_id].append((column, descriptor.label.value))
			n_edges = 0
			for row in self.query:
				if n_edges > max_edges:
					self._nodes.clear()
					self._attributes.clear()
					break
				obj_id1 = row.object.id
				for rel in row.object.relations:
					if rel.startswith("~"):
						continue
					for obj_id2 in ids_found.intersection(list(row.object.relations[rel])):
						G.add_edge(obj_id1, obj_id2, name = rel)
						n_edges += 1
		
		self._row_count = len(self._nodes)
		
		has_relations = set([])
		for obj_id1, obj_id2, k in G.edges(keys = True):
			self._edges.append([obj_id1, obj_id2, G.edges[obj_id1, obj_id2, k]["name"]])
			has_relations.add(obj_id1)
			has_relations.add(obj_id2)
		
		if not reset_positions:
			self._positions = self.graph_view.get_positions()
		
		g_positions = graphviz_layout(G, prog = "graphviz/dot.exe")
		xmax = 0
		todo = []
		for obj_id in G.nodes():
			if obj_id in has_relations:
				if obj_id not in self._positions:
					self._positions[obj_id] = g_positions[obj_id]
				xmax = max(xmax, self._positions[obj_id][0])
			else:
				todo.append(obj_id)
		xmax += 80
		for y, name in enumerate(todo):
			self._positions[name] = (xmax, y * 30)
		
		self.update_view(1)

	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def filter(self, text):
		
		pass
	
	def get_selected(self):
		
		return self._selection
	
	def get_selected_objects(self):
		
		objects, relations = self.graph_view.get_selected()
		objects = set(objects)
		for obj_id1, obj_id2, _ in relations:
			objects.add(obj_id1)
			objects.add(obj_id2)
		selected = {}
		for row, obj_id in enumerate(objects):
			selected[row] = self.model.objects[obj_id]
		return selected

	def get_objects(self):
		
		return [row.object for row in self.query]
	
	def get_row_count(self):
		
		return self._row_count
	
	def update_view(self, show_attributes):
		
		for n, name in [(0, "node_view"), (1, "value_view"), (2, "descriptor_view")]:
			self._actions[name].blockSignals(True)
			self._actions[name].setChecked(show_attributes == n)
			self._actions[name].blockSignals(False)
		self.graph_view.set_data(self._nodes, self._edges, self._attributes, self._positions, show_attributes = show_attributes)
		self.graph_view.reset_scene()
	
	def on_tool_triggered(self, action):
		
		fnc_name = "on_%s" % str(action.data())
		if hasattr(self, fnc_name):
			getattr(self, fnc_name)()
	
	def on_selected(self):
		
		objects, relations = self.graph_view.get_selected()
		# objects = [obj_id, ...]
		# relations [[obj_id1, obj_id2, rel], ...]
		
		self.parent.tab_lst.clear_selection()
		indexes = []
		row = 0
		for obj_id in objects:
			self.parent.tab_lst.select_object(obj_id)
			indexes.append(DModelIndex(row, 0, self.model.objects[obj_id]))
			row += 1
		for obj_id1, obj_id2, rel in relations:
			indexes.append(DModelIndex(row, 0, self.model.objects[obj_id2], self.model.objects[obj_id1].relations[rel]))
			row += 1
		self._selection = QuerySelection(self.model, self.view, indexes)
		self.broadcast(Broadcasts.VIEW_SELECTED)
		self.broadcast(Broadcasts.VIEW_ACTION)
		
	def on_activated(self, obj_id):
		
		self.parent.on_object_activated(self.model.objects[obj_id])
	
	# Toolbar actions
	
	def on_node_view(self):
		
		self.update_view(0)
	
	def on_value_view(self):
		
		self.update_view(1)
	
	def on_descriptor_view(self):
		
		self.update_view(2)
	
	def on_reset_layout(self):
		
		self.populate(reset_positions = True)
		self.graph_view.reset_scene()
	
	def on_zoom_in(self):
		
		self.graph_view.scale(1.1, 1.1)
	
	def on_zoom_out(self):
		
		self.graph_view.scale(0.9, 0.9)
	
	def on_zoom_reset(self):
		
		self.graph_view.reset_scene()
	
	def on_save_pdf(self):
		
		classes = [cls for cls in self.query.classes if "*" not in cls]
		if classes:
			name = classes[0]
		else:
			name = "objects"
		filename = "%s.pdf" % (name)
		path = self.view.registry.get("last_save_dir")
		if not path:
			path = os.path.join(str(Path.home()), "Desktop")
		path = os.path.join(path, filename)
		path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save As Adobe PDF", path, "Adobe PDF (*.pdf)")
		if not path:
			return
		self.view.registry.set("last_save_dir", os.path.split(path)[0])
		self.graph_view.save_pdf(path)

