from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.ClassVisMembers.GraphVisView import GraphVisView

from PySide2 import (QtWidgets, QtCore, QtGui)
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx

class ClassVis(Frame, QtWidgets.QMainWindow):
	
	def __init__(self, model, view, parent):
		
		self.actions = {} # {name: QAction, ...}
		
		self.nodes = {}  # {node_id: label, ...}
		self.edges = []  # [[source_id, target_id, label], ...]
		self.attributes = {}  # {node_id: [name, ...], ...}
		self.positions = {}  # {node_id: (x, y), ...}
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QMainWindow.__init__(self)
		
		self.set_up()
		
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_store_changed)
	
	def set_up(self):
		
		central_widget = QtWidgets.QWidget(self)
		central_widget.setLayout(QtWidgets.QVBoxLayout())
		central_widget.layout().setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(central_widget)
		
		self.set_up_toolbar()
		
		self.graph_view = GraphVisView()
		self.graph_view.activated.connect(self.on_activated)
		self.graph_view.selected.connect(self.on_selected)
		central_widget.layout().addWidget(self.graph_view)
		
		self.populate()
		self.graph_view.reset_scene()
		self.update_toolbar()
	
	def set_up_toolbar(self):
		
		self.toolbar = self.addToolBar("Graph")
		actions = [
			["descriptor_view", "Show Descriptors", "attributes.svg"],
			["reset_layout", "Re-arrange Layout", "geometry.svg"],
			["#separator", None, None],
			["add_class", "Add Class", "add_class.svg"],
			["add_descriptor", "Add Descriptor", "add_descriptor.svg"],
			["add_relation", "Add Relation", "link.svg"],
			["delete", "Delete", "delete.svg"],
			["#separator", None, None],
			["zoom_in", "Zoom In", "zoom_in.svg"],
			["zoom_out", "Zoom Out", "zoom_out.svg"],
			["zoom_reset", "Zoom Reset", "zoom_reset.svg"],
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
	
	def update_toolbar(self):
		
		classes, relations = self.get_selected()
		
		self.actions["add_descriptor"].setEnabled(len(classes) > 0)
		self.actions["add_relation"].setEnabled(len(classes) == 2)
		self.actions["delete"].setEnabled((len(classes) > 0) or (len(relations) > 0))
	
	def populate(self, positions = {}):
		
		self.nodes = {}  # {node_id: label, ...}
		self.edges = []  # [[source_id, target_id, label], ...]
		self.attributes = {}  # {node_id: [name, ...], ...}
		self.positions = {}  # {node_id: (x, y), ...}
		
		self.positions.update(positions)
		
		G = nx.MultiDiGraph()
		classes_done = set([])
		for name in self.model.classes:
			descriptors = sorted(list(self.model.classes[name].descriptors), key = lambda name2: self.model.classes[name2].order)
			G.add_node(name, descriptors = descriptors)
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
		g_positions = graphviz_layout(G, prog = "graphviz/dot.exe")
		
		for name in G.nodes():
			self.nodes[name] = name
			self.attributes[name] = G.nodes[name]["descriptors"]
			x, y = g_positions[name]
			self.positions[name] = (x, y)
		for name1, name2, k in G.edges(keys = True):
			if G.edges[name1, name2, k]["type"] == "Relation":
				self.edges.append([name1, name2, G.edges[name1, name2, k]["name"]])
		
		self.graph_view.set_data(self.nodes, self.edges, self.attributes, self.positions, show_attributes = self.actions["descriptor_view"].isChecked())

	def name(self):
		
		return "Class Relations"
	
	def icon(self):
		
		return "classes_graph.svg"
	
	def get_selected(self):
		
		classes, relations = self.graph_view.get_selected()
		# classes = [name, ...]
		# relations = [[name1, name2, label], ...]
		return classes, relations
	
	def get_objects(self):
		# re-implement to return a list of objects in order of rows
		
		return []
	
	def on_store_changed(self, *args):
		
		self.populate()
		self.update_toolbar()
	
	def on_tool_triggered(self, action):
		
		fnc_name = "on_%s" % str(action.data())
		if hasattr(self, fnc_name):
			getattr(self, fnc_name)()
	
	def on_selected(self):
		
		self.update_toolbar()
	
	def on_activated(self, name):
		
		if ("." in name) or (" " in name):
			name = "\"%s\"" % name
		self.view.query("SELECT %s.*" % (name))
	
	# Toolbar actions
	
	def on_descriptor_view(self):
		
		self.graph_view.set_data(self.nodes, self.edges, self.attributes, self.positions, show_attributes = self.actions["descriptor_view"].isChecked())
	
	def on_reset_layout(self):
		
		self.populate()
		self.update_toolbar()
	
	def on_add_class(self):
		
		self.view.dialogs.open("AddClass")
	
	def on_add_descriptor(self):
		
		classes, _ = self.graph_view.get_selected()
		self.view.dialogs.open("AddDescriptor", classes)
	
	def on_add_relation(self):
		
		classes, _ = self.get_selected()
		if len(classes) != 2:
			return
		cls1, cls2 = classes
		self.view.dialogs.open("AddRelationVis", cls1, cls2)
	
	def on_delete(self):
		
		classes, relations = self.get_selected()
		# classes = [name, ...]
		# relations = [[name1, name2, label], ...]
		
		reply = QtWidgets.QMessageBox.question(self, "Delete", "Delete all selected items?",
			QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
		if reply != QtWidgets.QMessageBox.Yes:
			return
		
		for cls1, cls2, rel in relations:
			self.model.classes[cls1].del_relation(rel, cls2)
		for cls in classes:
			del self.model.classes[cls]
	
	def on_zoom_in(self):
		
		self.graph_view.scale(1.1, 1.1)
	
	def on_zoom_out(self):
		
		self.graph_view.scale(0.9, 0.9)
	
	def on_zoom_reset(self):
		
		self.graph_view.reset_scene()
	
	
	
