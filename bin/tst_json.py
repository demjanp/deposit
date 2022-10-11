#!/usr/bin/env python

import networkx as nx
import json

import deposit
from deposit.query.query import Query

from deposit.store.abstract_delement import AbstractDElement
from deposit.store.dobject import DObject
from deposit.store.dclass import DClass

class DJSONEncoder(json.JSONEncoder):
	
	def default(self, o):
		
		if isinstance(o, AbstractDElement):
			data = o.to_dict()
			data["dcls"] = o.__class__.__name__
			return data
		return o.__dict__

def decode_delements(store, data):
	
	if "dcls" in data:
		if data["dcls"] == "DObject":
			return DObject(store, data["id"]).from_dict_1(data)
		if data["dcls"] == "DClass":
			return DClass(store, data["name"], data["order"]).from_dict_1(data)
	return data

if __name__ == "__main__":
	
	store = deposit.Store()
	
#	for i in range(30): # 1 - 30
#		store.add_object()
	
	finds = store.add_class("Find")
	features = store.add_class("Feature")
	areas = store.add_class("Area.X")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	fe13 = features.add_member()
	fe13.set_descriptor("Name", "A1.F3")
	fe24 = features.add_member()
	fe24.set_descriptor("Name", "A2.F4")
	fe25 = features.add_member()
	fe25.set_descriptor("Name", "A2.F5")
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	f121 = finds.add_member()
	f121.set_descriptor("Name", "A1.F2.1")
	f122 = finds.add_member()
	f122.set_descriptor("Name", "A1.F2.2")
	f131 = finds.add_member()
	f131.set_descriptor("Name", "A1.F3.1")
	f241 = finds.add_member()
	f241.set_descriptor("Name", {"area:": "A2", "feature": "F4", "find": 1})
	
	a1.add_relation(fe11, "contains")
	a1.add_relation(fe12, "contains")
	a1.add_relation(fe13, "contains")
	a2.add_relation(fe24, "contains")
	a2.add_relation(fe25, "contains")
	
	fe11.add_relation(f111, "contains")
	fe11.add_relation(f112, "contains")
	fe12.add_relation(f121, "contains")
	fe12.add_relation(f122, "contains")
	fe13.add_relation(f131, "contains")
	fe24.add_relation(f241, "contains")
	
	fe11.add_relation(fe12, "disturbs")
	fe11.add_relation(fe12, "descr")
	fe24.add_relation(fe25, "disturbs")
	
	
	datas = json.dumps(dict(
		object_relations = nx.node_link_data(store._GOR), 
		class_relations = nx.node_link_data(store._GCR), 
		class_membership = nx.node_link_data(store._GCM), 
		max_order = store._max_order,
#		changed = changed,
#		events = events,
#		user_tools = user_tools,
#		queries = queries,
#		deposit_version = deposit_version,
	), cls = DJSONEncoder)
	
	print()
	print(datas)
	print()
	
	#--------------------------------------------------
	
	store = None
	store = deposit.Store()
	
	data = json.loads(datas, object_hook = lambda data: decode_delements(store, data))
	store._GOR = nx.node_link_graph(data["object_relations"], directed = True, multigraph = True)
	store._GCR = nx.node_link_graph(data["class_relations"], directed = True, multigraph = True)
	store._GCM = nx.node_link_graph(data["class_membership"], directed = True, multigraph = False)
	for G in [store._GOR, store._GCR]:
		for key in G.nodes:
			G.nodes[key]["data"].from_dict_2()
	store._max_order = data["max_order"]
	
	query = Query(store, "SELECT [Area.X].Name, Feature.Name, Find.Name")
	print()
	print(query.columns)
	print()
	for row in query:
		print(row)
	print()
