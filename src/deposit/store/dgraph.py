import warnings
with warnings.catch_warnings():
	 warnings.simplefilter("ignore")
	 import networkit as nk
import networkx as nx
from itertools import product

class DGraph(object):
	
	def __init__(self):
		
		self._GOR = None			# Object relation graph (edge = relation)
		self._GCR = None			# Class relation graph (edge = relation)
		self._GCM = None			# Class membership graph (edge = contains)
		
		self._GOR_names = {}		# {node_id: obj_id, ...}
		self._GOR_lookup = {}		# {obj_id: node_id, ...}
		self._GOR_data = {}  		# {obj_id: data, ...}
		self._GOR_labels = {}		# {(src_id, tgt_id): {label: weight, ...}, ...}
		
		self._GCR_names = {}		# {node_id: name, ...}
		self._GCR_lookup = {}		# {name: node_id, ...}
		self._GCR_data = {}  		# {name: data, ...}
		self._GCR_labels = {}		# {(src_id, tgt_id): [label, ...], ...}
		
		self._GCM_names = {}		# {node_id: name/obj_id, ...}
		self._GCM_lookup = {}		# {name/obj_id: node_id, ...}
		
		self.clear()
	
	def n_objects(self):
		
		return self._GOR.numberOfNodes()
	
	def n_classes(self):
		
		return self._GCR.numberOfNodes()
	
	def clear(self):
		
		self._GOR = nk.graph.Graph(directed = True)
		self._GCR = nk.graph.Graph(directed = True)
		self._GCM = nk.graph.Graph(directed = True)
		
		self._GOR_names.clear()
		self._GOR_lookup.clear()
		self._GOR_data.clear()
		self._GOR_labels.clear()
		
		self._GCR_names.clear()
		self._GCR_lookup.clear()
		self._GCR_data.clear()
		self._GCR_labels.clear()
		
		self._GCM_names.clear()
		self._GCM_lookup.clear()
	
	
	# ---- Objects
	# ------------------------------------------------------------------------
	
	def iter_objects(self):
		
		for obj_id in self._GOR_lookup:
			yield obj_id
	
	def iter_objects_data(self):
		
		for obj_id in self._GOR_data:
			yield self._GOR_data[obj_id]
	
	def iter_object_parents(self, obj_id):
		
		node_id = self._GCM_lookup[obj_id]
		for src in self._GCM.iterInNeighbors(node_id):
			yield self._GCM_names[src]
	
	def iter_object_ancestors(self, obj_id):
		
		node_id = self._GCM_lookup[obj_id]
		ancestors = set()
		queue = set([node_id])
		while queue:
			for src in self._GCM.iterInNeighbors(queue.pop()):
				if src not in ancestors:
					queue.add(src)
				ancestors.add(src)
		for node in ancestors:
			yield self._GCM_names[node]
	
	def has_object(self, obj_id):
		
		return obj_id in self._GOR_lookup
	
	def add_object(self, obj_id, data):
		
		if obj_id not in self._GOR_lookup:
			node_id = self._GOR.addNode()
			self._GOR_lookup[obj_id] = node_id
			self._GOR_names[node_id] = obj_id
			node_id = self._GCM.addNode()
			self._GCM_lookup[obj_id] = node_id
			self._GCM_names[node_id] = obj_id
		self._GOR_data[obj_id] = data
	
	def get_object_data(self, obj_id):
		
		return self._GOR_data[obj_id]
	
	def iter_object_relations(self, obj_id = None):
		
		if obj_id is None:
			for src, tgt in self._GOR.iterEdges():
				for label in self._GOR_labels[(src, tgt)]:
					yield self._GOR_names[src], self._GOR_names[tgt], label
		else:
			if obj_id not in self._GOR_lookup:
				return []
			node_id = self._GOR_lookup[obj_id]
			for tgt in self._GOR.iterNeighbors(node_id):
				for label in self._GOR_labels[(node_id, tgt)]:
					yield self._GOR_names[tgt], label
	
	def add_object_relation(self, src_id, tgt_id, label, weight = None):
		
		src_id = self._GOR_lookup[src_id]
		tgt_id = self._GOR_lookup[tgt_id]
		
		if not self._GOR.hasEdge(src_id, tgt_id):
			self._GOR.addEdge(src_id, tgt_id)
			self._GOR_labels[(src_id, tgt_id)] = {}
		self._GOR_labels[(src_id, tgt_id)][label] = weight
	
	def has_object_relation(self, src_id, tgt_id, label):
		
		src_id = self._GOR_lookup[src_id]
		tgt_id = self._GOR_lookup[tgt_id]
		
		if not self._GOR.hasEdge(src_id, tgt_id):
			return False
		if label == "*":
			return True
		return label in self._GOR_labels[(src_id, tgt_id)]
	
	def get_object_relation_weight(self, src_id, tgt_id, label):
		
		src_id = self._GOR_lookup[src_id]
		tgt_id = self._GOR_lookup[tgt_id]
		
		if not self._GOR.hasEdge(src_id, tgt_id):
			return None
		return self._GOR_labels[(src_id, tgt_id)].get(label, None)
	
	def del_object_relation(self, src_id, tgt_id, label):
		
		src_id = self._GOR_lookup[src_id]
		tgt_id = self._GOR_lookup[tgt_id]
		
		if not self._GOR.hasEdge(src_id, tgt_id):
			return
		if label in self._GOR_labels[(src_id, tgt_id)]:
			del self._GOR_labels[(src_id, tgt_id)][label]
		if not self._GOR_labels[(src_id, tgt_id)]:
			self._GOR.removeEdge(src_id, tgt_id)
			del self._GOR_labels[(src_id, tgt_id)]
	
	def del_object(self, obj_id):
		
		node_id = self._GOR_lookup[obj_id]
		del self._GOR_names[node_id]
		del self._GOR_lookup[obj_id]
		del self._GOR_data[obj_id]
		for tgt in self._GOR.iterNeighbors(node_id):
			if (node_id, tgt) in self._GOR_labels:
				del self._GOR_labels[(node_id, tgt)]
		for src in self._GOR.iterInNeighbors(node_id):
			if (src, node_id) in self._GOR_labels:
				del self._GOR_labels[(src, node_id)]
		self._GOR.removeNode(node_id)
		
		node_id = self._GCM_lookup[obj_id]
		self._GCM.removeNode(node_id)
		del self._GCM_names[node_id]
		del self._GCM_lookup[obj_id]
	
	
	# ---- Classes
	# ------------------------------------------------------------------------
	
	def iter_classes(self):
		
		for name in self._GCR_lookup:
			yield name
	
	def iter_classes_data(self):
		
		for name in self._GCR_data:
			yield self._GCR_data[name]
	
	def has_class(self, name):
		
		return name in self._GCR_lookup
	
	def add_class(self, name, data):
		
		if name not in self._GCR_lookup:
			node_id = self._GCR.addNode()
			self._GCR_lookup[name] = node_id
			self._GCR_names[node_id] = name
			node_id = self._GCM.addNode()
			self._GCM_lookup[name] = node_id
			self._GCM_names[node_id] = name
		self._GCR_data[name] = data
	
	def rename_class(self, name, new_name):
		
		node_id = self._GCR_lookup[name]
		data = self._GCR_data[name]
		del self._GCR_lookup[name]
		del self._GCR_data[name]
		self._GCR_names[node_id] = new_name
		self._GCR_lookup[new_name] = node_id
		self._GCR_data[new_name] = data
		
		node_id = self._GCM_lookup[name]
		del self._GCM_lookup[name]
		self._GCM_names[node_id] = new_name
		self._GCM_lookup[new_name] = node_id
	
	def get_class_data(self, name):
		
		return self._GCR_data[name]
	
	def iter_class_children(self, name):
		
		node_id = self._GCM_lookup[name]
		for tgt in self._GCM.iterNeighbors(node_id):
			yield self._GCM_names[tgt]
	
	def iter_class_descendants(self, name):
		
		node_id = self._GCM_lookup[name]
		descendants = set()
		nk.traversal.Traversal.DFSfrom(self._GCM, node_id, lambda node: descendants.add(node))
		descendants.remove(node_id)
		for node in descendants:
			yield self._GCM_names[node]
	
	def iter_class_parents(self, child):
		
		if child not in self._GCM_lookup:
			return []
		node_id = self._GCM_lookup[child]
		for src in self._GCM.iterInNeighbors(node_id):
			yield self._GCM_names[src]
	
	def iter_class_ancestors(self, child):
		
		node_id = self._GCM_lookup[child]
		ancestors = set()
		queue = set([node_id])
		while queue:
			for src in self._GCM.iterInNeighbors(queue.pop()):
				if src not in ancestors:
					queue.add(src)
				ancestors.add(src)
		for node in ancestors:
			yield self._GCM_names[node]
	
	def iter_class_relations(self, name = None):
		
		if name is None:
			for src, tgt in self._GCR.iterEdges():
				if (src, tgt) in self._GCR_labels:
					for label in self._GCR_labels[(src, tgt)]:
						yield self._GCR_names[src], self._GCR_names[tgt], label
		else:
			node_id = self._GCR_lookup[name]
			for tgt in self._GCR.iterNeighbors(node_id):
				if (node_id, tgt) in self._GCR_labels:
					for label in self._GCR_labels[(node_id, tgt)]:
						yield self._GCR_names[tgt], label
	
	def shortest_path_between_classes(self, src, tgt):
		# src / tgt = class_name or set(obj_id, ...)
		
		def _get_GOR_ids(name):
			
			if isinstance(name, set):
				return set([self._GOR_lookup[obj_id] for obj_id in name])
			elif name in self._GCM_lookup:
				collect = set()
				for node_id in self._GCM.iterNeighbors(self._GCM_lookup[name]):
					obj_id = self._GCM_names[node_id]
					if isinstance(obj_id, int):
						collect.add(self._GOR_lookup[obj_id])
				return collect
			return set()
		
		if (not isinstance(src, set)) and (not isinstance(tgt, set)) and \
			(src in self._GCR_lookup) and (tgt in self._GCR_lookup):
				src_id = self._GCR_lookup[src]
				tgt_id = self._GCR_lookup[tgt]
				
				bi_dij = nk.distance.BidirectionalDijkstra(self._GCR, src_id, tgt_id)
				bi_dij.run()
				
				path = [self._GCR_names[node_id] for node_id in bi_dij.getPath()]
				if path:
					return path
		
		path_opt = None
		nodes_src = _get_GOR_ids(src)
		nodes_tgt = _get_GOR_ids(tgt)
		nodes_src, nodes_tgt = nodes_src.difference(nodes_tgt), nodes_tgt.difference(nodes_src)
		if nodes_src and nodes_tgt:
			for node_src, node_tgt in product(nodes_src, nodes_tgt):
				bi_dij = nk.distance.BidirectionalDijkstra(self._GOR, node_src, node_tgt)
				bi_dij.run()
				path = [node_src] + bi_dij.getPath() + [node_tgt]
				if len(path) < 2:
					continue
				if (len(path) > 1) and ((path_opt is None) or (len(path) < len(path_opt))):
					path_opt = path
				if len(path_opt) == 2:
					break
		
		collect = []
		if path_opt is not None:
			for node_id in path_opt:
				for src_ in self._GCM.iterInNeighbors(self._GCM_lookup[self._GOR_names[node_id]]):
					name = self._GCM_names[src_]
					if name not in collect:
						collect.append(name)
		return collect
	
	def add_class_child(self, name, child):
		# child = obj_id or subclass_name
		
		src_id = self._GCM_lookup[name]
		tgt_id = self._GCM_lookup[child]
		if not self._GCM.hasEdge(src_id, tgt_id):
			self._GCM.addEdge(src_id, tgt_id)
	
	def has_class_child(self, name, child):
		# child = obj_id or subclass_name
		
		src_id = self._GCM_lookup[name]
		tgt_id = self._GCM_lookup[child]
		
		return self._GCM.hasEdge(src_id, tgt_id)
	
	def has_class_relation(self, src_name, tgt_name, label):
		
		src_id = self._GCR_lookup[src_name]
		tgt_id = self._GCR_lookup[tgt_name]
		
		if not self._GCR.hasEdge(src_id, tgt_id):
			return False
		
		return label in self._GCR_labels[(src_id, tgt_id)]
	
	def add_class_relation(self, src_name, tgt_name, label):
		
		src_id = self._GCR_lookup[src_name]
		tgt_id = self._GCR_lookup[tgt_name]
		
		if not self._GCR.hasEdge(src_id, tgt_id):
			self._GCR.addEdge(src_id, tgt_id)
			self._GCR_labels[(src_id, tgt_id)] = []
		if label not in self._GCR_labels[(src_id, tgt_id)]:
			self._GCR_labels[(src_id, tgt_id)].append(label)
	
	def del_class_relation(self, src_name, tgt_name, label):
		
		src_id = self._GCR_lookup[src_name]
		tgt_id = self._GCR_lookup[tgt_name]
		
		if not self._GCR.hasEdge(src_id, tgt_id):
			return
		if label in self._GCR_labels[(src_id, tgt_id)]:
			self._GCR_labels[(src_id, tgt_id)].remove(label)
		if not self._GCR_labels[(src_id, tgt_id)]:
			self._GCR.removeEdge(src_id, tgt_id)
			del self._GCR_labels[(src_id, tgt_id)]
	
	def del_class_child(self, name, child):
		# child = obj_id or subclass_name
		
		src_id = self._GCM_lookup[name]
		tgt_id = self._GCM_lookup[child]
		if self._GCM.hasEdge(src_id, tgt_id):
			self._GCM.removeEdge(src_id, tgt_id)
	
	def del_class(self, name):
		
		node_id = self._GCR_lookup[name]
		del self._GCR_names[node_id]
		del self._GCR_lookup[name]
		del self._GCR_data[name]
		for tgt in self._GCR.iterNeighbors(node_id):
			if (node_id, tgt) in self._GCR_labels:
				del self._GCR_labels[(node_id, tgt)]
		for src in self._GCR.iterInNeighbors(node_id):
			if (src, node_id) in self._GCR_labels:
				del self._GCR_labels[(src, node_id)]
		self._GCR.removeNode(node_id)
		
		node_id = self._GCM_lookup[name]
		self._GCM.removeNode(node_id)
		del self._GCM_names[node_id]
		del self._GCM_lookup[name]
	
	
	# ---- Serialize
	# ------------------------------------------------------------------------
	
	def objects_to_nx(self):
		
		G = nx.MultiDiGraph()
		for obj_id in self._GOR_data:
			G.add_node(obj_id, data = self._GOR_data[obj_id])
		for src_id, tgt_id in self._GOR_labels:
			for label in self._GOR_labels[(src_id, tgt_id)]:
				weight = self._GOR_labels[(src_id, tgt_id)][label]
				if weight is None:
					G.add_edge(self._GOR_names[src_id], self._GOR_names[tgt_id], label)
				else:
					G.add_edge(self._GOR_names[src_id], self._GOR_names[tgt_id], label, weight = weight)
		return G
	
	def classes_to_nx(self):
		
		G = nx.MultiDiGraph()
		for name in self._GCR_data:
			G.add_node(name, data = self._GCR_data[name])
		for src_id, tgt_id in self._GCR_labels:
			for label in self._GCR_labels[(src_id, tgt_id)]:
				G.add_edge(self._GCR_names[src_id], self._GCR_names[tgt_id], label)
		return G
	
	def members_to_nx(self):
		
		G = nx.DiGraph()
		for name in self._GCM_lookup:
			G.add_node(name)
		for src_id, tgt_id in self._GCM.iterEdges():
			G.add_edge(self._GCM_names[src_id], self._GCM_names[tgt_id])
		return G
	
	def objects_from_nx(self, G):
		
		self._GOR = nk.graph.Graph(directed = True)
		self._GOR_names = {}		# {node_id: obj_id, ...}
		self._GOR_lookup = {}		# {obj_id: node_id, ...}
		self._GOR_data = {}  		# {obj_id: data, ...}
		self._GOR_labels = {}		# {(src_id, tgt_id): [[label, weight], ...], ...}
		for obj_id, data in G.nodes(data = "data"):
			node_id = self._GOR.addNode()
			self._GOR_lookup[obj_id] = node_id
			self._GOR_names[node_id] = obj_id
			self._GOR_data[obj_id] = data
		for src_id, tgt_id, label in G.edges(keys = True):
			weight = G.edges[src_id, tgt_id, label].get("weight", None)
			src_id = self._GOR_lookup[src_id]
			tgt_id = self._GOR_lookup[tgt_id]
			if not self._GOR.hasEdge(src_id, tgt_id):
				self._GOR.addEdge(src_id, tgt_id)
				self._GOR_labels[(src_id, tgt_id)] = {}
			self._GOR_labels[(src_id, tgt_id)][label] = weight
		
	def classes_from_nx(self, G):
		
		self._GCR = nk.graph.Graph(directed = True)
		self._GCR_names = {}		# {node_id: name, ...}
		self._GCR_lookup = {}		# {name: node_id, ...}
		self._GCR_data = {}  		# {name: data, ...}
		self._GCR_labels = {}		# {(src_id, tgt_id): [[label, weight], ...], ...}
		for name, data in G.nodes(data = "data"):
			node_id = self._GCR.addNode()
			self._GCR_lookup[name] = node_id
			self._GCR_names[node_id] = name
			self._GCR_data[name] = data
		for src_id, tgt_id, label in G.edges(keys = True):
			src_id = self._GCR_lookup[src_id]
			tgt_id = self._GCR_lookup[tgt_id]
			if not self._GCR.hasEdge(src_id, tgt_id):
				self._GCR.addEdge(src_id, tgt_id)
				self._GCR_labels[(src_id, tgt_id)] = []
			self._GCR_labels[(src_id, tgt_id)].append(label)
	
	def members_from_nx(self, G):
		
		self._GCM = nk.graph.Graph(directed = True)
		self._GCM_names = {}		# {node_id: name/obj_id, ...}
		self._GCM_lookup = {}		# {name/obj_id: node_id, ...}
		for name in G.nodes():
			node_id = self._GCM.addNode()
			self._GCM_lookup[name] = node_id
			self._GCM_names[node_id] = name
		for src_id, tgt_id in G.edges():
			src_id = self._GCM_lookup[src_id]
			tgt_id = self._GCM_lookup[tgt_id]
			self._GCM.addEdge(src_id, tgt_id)
		
	
	def objects_to_json(self, graph_attrs):
		
		return nx.node_link_data(self.objects_to_nx(), attrs = graph_attrs)
	
	def classes_to_json(self, graph_attrs):
		
		return nx.node_link_data(self.classes_to_nx(), attrs = graph_attrs)
	
	def members_to_json(self, graph_attrs):
		
		return nx.node_link_data(self.members_to_nx(), attrs = graph_attrs)
	
	def objects_from_json(self, data, graph_attrs):
		
		G = nx.node_link_graph(data, directed = True, multigraph = True, attrs = graph_attrs)
		self.objects_from_nx(G)
	
	def classes_from_json(self, data, graph_attrs):
		
		G = nx.node_link_graph(data, directed = True, multigraph = True, attrs = graph_attrs)
		self.classes_from_nx(G)
	
	def members_from_json(self, data, graph_attrs):
		
		G = nx.node_link_graph(data, directed = True, multigraph = False, attrs = graph_attrs)
		self.members_from_nx(G)
	
	def _graph_to_pickle(self, G, names):
		
		nodes = list(names.values())
		edges = []
		for node_src, node_tgt in G.iterEdges():
			edges.append((names[node_src], names[node_tgt]))
		
		return [nodes, edges]
	
	def _labels_to_pickle(self, labels, names):
		
		data = {}
		for key in labels:
			node_src, node_tgt = key
			data[(names[node_src], names[node_tgt])] = labels[key]
		return data
	
	def _graph_from_pickle(self, data):
		
		nodes, edges = data
		G = nk.graph.Graph(directed = True)
		G.addNodes(len(nodes))
		names = {}
		lookup = {}
		for i, name in enumerate(nodes):
			names[i] = name
			lookup[name] = i
		for name_src, name_tgt in edges:
			G.addEdge(lookup[name_src], lookup[name_tgt])
		
		return G, names, lookup
	
	def _labels_from_pickle(self, labels, lookup):
		
		data = {}
		for key in labels:
			name_src, name_tgt = key
			data[(lookup[name_src], lookup[name_tgt])] = labels[key]
		
		return data
	
	def objects_to_pickle(self):
		
		return [
			self._graph_to_pickle(self._GOR, self._GOR_names),
			self._GOR_data,
			self._labels_to_pickle(self._GOR_labels, self._GOR_names),
		]
	
	def classes_to_pickle(self):
		
		return [
			self._graph_to_pickle(self._GCR, self._GCR_names),
			self._GCR_data,
			self._labels_to_pickle(self._GCR_labels, self._GCR_names),
		]
	
	def members_to_pickle(self):
		
		return self._graph_to_pickle(self._GCM, self._GCM_names)
	
	def objects_from_pickle(self, data):
		
		[
			graph_data,
			self._GOR_data,
			labels,
		] = data
		self._GOR, self._GOR_names, self._GOR_lookup = self._graph_from_pickle(graph_data)
		self._GOR_labels = self._labels_from_pickle(labels, self._GOR_lookup)
	
	def classes_from_pickle(self, data):
		
		[
			graph_data,
			self._GCR_data,
			labels,
		] = data
		self._GCR, self._GCR_names, self._GCR_lookup = self._graph_from_pickle(graph_data)
		self._GCR_labels = self._labels_from_pickle(labels, self._GCR_lookup)
	
	def members_from_pickle(self, data):
		
		self._GCM, self._GCM_names, self._GCM_lookup = self._graph_from_pickle(data)

