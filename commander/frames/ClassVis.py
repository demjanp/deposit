from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.GraphVisView import (GraphVisView)
from deposit.commander.frames.QueryMembers.QueryItem import (DModelIndex)
from deposit.commander.frames.QueryMembers.QuerySelection import (QuerySelection)

from PySide2 import (QtWidgets, QtCore, QtGui)
from networkx.drawing.nx_agraph import graphviz_layout
from pathlib import Path
import networkx as nx
import os

class ClassVis(Frame, QtWidgets.QMainWindow):
	
	def __init__(self, model, view, parent):
		
		self.actions = {} # {name: QAction, ...}
		
		self.nodes = {}  # {node_id: label, ...}
		self.edges = []  # [[source_id, target_id, label], ...]
		self.attributes = {}  # {node_id: [(name, value), ...], ...}
		self.positions = {}  # {node_id: (x, y), ...}
		
		self._selection = None
		
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
		
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_ADDED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_DELETED, self.on_store_changed)
		
	def set_up(self):
		
		self.populate()
	
	def set_up_toolbar(self):
		
		self.toolbar = self.addToolBar("Graph")
		actions = [
			["descriptor_view", "Show Descriptors", "attributes.svg"],
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
				self.actions[name] = QtWidgets.QAction(self.view.get_icon(icon), text, self)
				self.actions[name].setData(name)
				self.toolbar.addAction(self.actions[name])
		
		self.actions["descriptor_view"].setCheckable(True)
		
		self.toolbar.actionTriggered.connect(self.on_tool_triggered)
	
	def populate(self, reset_positions = False):
		
		self.nodes.clear()
		self.edges.clear()
		self.attributes.clear()
		self.positions.clear()
		
		G = nx.MultiDiGraph()
		classes_done = set([])
		descriptors = set(self.model.descriptor_names)
		for name in self.model.classes:
			if name in descriptors:
				continue
			self.nodes[name] = name
			G.add_node(name)
			self.attributes[name] = [(name2, "") for name2 in sorted(list(self.model.classes[name].descriptors), key = lambda name2: self.model.classes[name2].order)]
			classes_done.add(name)
		for name in self.model.classes:
			cls = self.model.classes[name]
			for name2 in cls.subclasses:
				G.add_edge(name2, name, type = "Member")
			for rel in cls.relations:
				if rel.startswith("~"):
					continue
				for name2 in cls.relations[rel]:
					if name2 not in classes_done:
						continue
					G.add_edge(name, name2, type = "Relation", name = rel)
		
		has_relations = set([])
		for name1, name2, k in G.edges(keys = True):
			if G.edges[name1, name2, k]["type"] == "Relation":
				self.edges.append([name1, name2, G.edges[name1, name2, k]["name"]])
				has_relations.add(name1)
				has_relations.add(name2)
		
		if not reset_positions:
			self.positions = self.graph_view.get_positions()
		
		g_positions = graphviz_layout(G, prog = "graphviz/dot.exe")
		xmax = 0
		todo = []
		for name in G.nodes():
			if name in has_relations:
				if name not in self.positions:
					self.positions[name] = g_positions[name]
				xmax = max(xmax, self.positions[name][0])
			else:
				todo.append(name)
		xmax += 80
		for y, name in enumerate(todo):
			self.positions[name] = (xmax, y * 30)
		
		self.graph_view.set_data(self.nodes, self.edges, self.attributes, self.positions, show_attributes = 2 if self.actions["descriptor_view"].isChecked() else 0)

	def name(self):
		
		return "Class Relations"
	
	def icon(self):
		
		return "classes_graph.svg"
	
	def get_selected(self):
		
		return self._selection
	
	def get_objects(self):
		# re-implement to return a list of objects in order of rows
		
		return []
	
	def on_store_changed(self, *args):
		
		self.populate()
	
	def on_tool_triggered(self, action):
		
		fnc_name = "on_%s" % str(action.data())
		if hasattr(self, fnc_name):
			getattr(self, fnc_name)()
	
	def on_selected(self):
		
		classes, relations = self.graph_view.get_selected()
		# classes = [name, ...]
		# relations = [[name1, name2, rel], ...]
		
		indexes = []
		row = 0
		for name in classes:
			indexes.append(DModelIndex(row, 0, self.model.classes[name]))
			row += 1
		for name1, name2, rel in relations:
			indexes.append(DModelIndex(row, 0, self.model.classes[name1], (rel, name2)))
			row += 1
		self._selection = QuerySelection(self.model, self.view, indexes)
		self.broadcast(Broadcasts.VIEW_SELECTED)
		self.broadcast(Broadcasts.VIEW_ACTION)
	
	def on_activated(self, name):
		
		if ("." in name) or (" " in name):
			name = "\"%s\"" % name
		self.view.query("SELECT %s.*" % (name))
	
	# Toolbar actions
	
	def on_descriptor_view(self):
		
		self.graph_view.set_data(self.nodes, self.edges, self.attributes, self.positions, show_attributes = 2 if self.actions["descriptor_view"].isChecked() else 0)
		self.graph_view.reset_scene()
	
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
		
		filename = "%s_schema.pdf" % (os.path.split(str(self.model.identifier))[-1].strip("#"))
		path = self.view.registry.get("last_save_dir")
		if not path:
			path = os.path.join(str(Path.home()), "Desktop")
		path = os.path.join(path, filename)
		path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save As Adobe PDF", path, "Adobe PDF (*.pdf)")
		if not path:
			return
		self.view.registry.set("last_save_dir", os.path.split(path)[0])
		self.graph_view.save_pdf(path)

