import networkit as nk
import deposit

from itertools import combinations
import numpy as np
import pickle
import time

N_NODES = 1000000

if __name__ == "__main__":
	
	'''
	store = deposit.Store()
	store.load(path = "c:/data_processed/test_db_medium/test_db_medium.pickle")
	
	objs = np.random.choice(list(store.get_objects()), 100)
	combs = list(combinations(objs, 2))
	for obj1, obj2 in combs:
		obj1.add_relation(obj2, "dist", weight = round(np.random.random(), 3))
	'''
	
	G = nk.graph.Graph(directed = True)
	
	G.addNodes(10)
	
	for node_id in G.iterNodes():
		print(node_id)

