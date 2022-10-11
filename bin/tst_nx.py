import networkx as nx

class DObject(object):
	
	def __init__(self, obj_id, GOR, GCM):
		
		self.id = obj_id
		
		self._GOR = GOR
		self._GCM = GCM
		self._descriptors = {}
	
	def get_classes(self):
		
		for name, cls in self._GCM.nodes(data = "data"):
			yield cls

class DClass(object):
	
	def __init__(self, name, GCR, GCM):
		
		self._name = name
		self._GCR = GCR
		self._GCM = GCM
		

if __name__ == "__main__":
	
	GOR = nx.MultiDiGraph()
	GCR = nx.MultiDiGraph()
	GCM = nx.DiGraph()
	
	
	cls = DClass("A", GCR, GCM)
	GCR.add_node("A", data = cls)
	GCM.add_node("A", data = cls)
	
	obj = DObject(1, GOR, GCM)
	GOR.add_node(1, data = obj)
	GCM.add_node(1, data = obj)
	
	GOR.nodes[1]["data"]._descriptors["dA1"] = 1.0
	
	for obj_id, obj in GOR.nodes(data = "data"):
		print(obj_id, obj._descriptors)
		for i in range(5):
			for cls in obj.get_classes():
				obj._descriptors["dA1"] += 0.1
				if isinstance(cls, DObject):
					print("\t", cls.id, cls._descriptors)
				else:
					print("\t", cls)
	