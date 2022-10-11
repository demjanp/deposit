import deposit
import networkx as nx
from deposit.store.abstract_delement import AbstractDElement

if __name__ == "__main__":
	
	store = deposit.Store()
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F1",
		},
		relations = set([
			("Area", "contains", "Feature"),
		]),
	)
	
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F2",
		},
		relations = set([
			("Area", "contains", "Feature"),
		]),
	)
	
	cls = store.get_class("Area")
	cls.add_relation("Feature", "contains")
	
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F3",
		},
	)
	
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F3",
		},
		unique = set(["Feature"])
	)
	
	store.add_data_row(
		data = {
			("Feature", "Name"): "A1.F4",
		},
		unique = set([])
	)
	
	data = nx.node_link_data(store._GOR)
	for node_data in data["nodes"]:
		if isinstance(node_data["data"], AbstractDElement):
			print(node_data["data"].to_dict())

