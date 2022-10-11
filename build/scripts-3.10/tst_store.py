#!/usr/bin/env python

import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	
	store.add_object()  # 1
	store.add_object()  # 2
	store.add_object()  # 3
	store.add_object()  # 4
	store.add_object()  # 5
	store.add_object()  # 6
	store.add_object()  # 7
	store.add_object()  # 8
	
	store.add_class("Cls A")
	store.add_class("Cls B")
	store.add_class("Cls C")
	
	store.add_member("Cls A", 1)
	store.add_member("Cls A", 2)
	store.add_member("Cls A", 8)
	
	store.add_member("Cls B", 3)
	store.add_member("Cls B", 4)
	
	store.add_member("Cls C", 5)
	store.add_member("Cls C", 6)
	store.add_member("Cls C", 7)
	
	store.add_subclass("Cls B", "Cls A")
	
	store.add_relation(1, 3, "A-B")
	store.add_relation(1, 4, "A-B")
	store.add_relation(2, 1, "A-A", weight = 0.123)
	store.add_relation(3, 5, "B-C")
	store.add_relation(3, 6, "B-C")
	store.add_relation(3, 7, "B-C")
	
	store.add_class_relation("Cls A", "Cls B", "ClsA-B")
	
	store.del_subclass("Cls B", "Cls A")
	
	store.add_descriptor(1, "Descr A1", 1)
	store.add_descriptor(1, "Descr A2", "X")
	store.add_descriptor(2, "Descr A1", 1.1)
	store.add_descriptor(3, "Descr B", {"value": 2})
	
	store.add_class_descriptor("Cls A", "Descr C_A1")
	store.add_class_descriptor("Cls A", "Descr C_A2")
	store.add_class_descriptor("Cls B", "Descr C_B")
	
#	store.rename_class("Cls A", "Cls A_")
	
#	print(sorted(list(store.get_connected(1, "Cls C"))))
	
	for path in store.get_connected(2, "Cls C"):
		print(path)
	
	'''
	print()
	print("Nodes:")
	for key in store._graph.nodes:
		print(key, store._graph.nodes[key])
	print()
	print("Edges:")
	for key in store._graph.edges:
		print(key, store._graph.edges[key])
	print()
	'''
