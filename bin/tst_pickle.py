#!/usr/bin/env python

import deposit
from deposit.query.query import Query

import pickle

if __name__ == "__main__":
	
	store = deposit.Store()
	
#	for i in range(30): # 1 - 30
#		store.add_object()
	
	finds = store.add_class("Find")
	features = store.add_class("Feature")
	areas = store.add_class("Area")
	
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
	f241.set_descriptor("Name", "A2.F4.1")
	
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
	fe24.add_relation(fe25, "disturbs")
	
#	store.add_relation(2, 3, "disturbs")
#	store.add_relation(4, 3, "disturbs")
	
	'''
	with open("temp.pickle", "wb") as f:
		pickle.dump([
			store._GOR, 
			store._GCR, 
			store._GCM, 
			store._max_order
#			changed,
#			events,
#			user_tools,
#			queries,
#			deposit_version,
		], f, pickle.HIGHEST_PROTOCOL)
	'''
	
	resp = store.save("Pickle", "test_db/temp.pickle")
	print("saved:", resp)
	
#	store = None
#	store = deposit.Store()
	store.clear()
	
	resp = store.load("Pickle", "test_db/temp.pickle")
	print("loaded:", resp)
	
	'''
	with open("temp.pickle", "rb") as f:
		store._GOR, store._GCR, store._GCM, store._max_order = pickle.load(f)
	'''
	
#	query = Query(store, "SELECT Area, Feature, COUNT(Find) AS [Cnt Find] GROUP BY Area, Feature")
#	query = Query(store, "SELECT Area.Name, Feature.Name, Find.Name WHERE (Area is not None) and (Find.Name is not None) and Find.Name.startswith('A1.F1.')")
#	query = Query(store, "SELECT Area.Name, Feature.Name WHERE (Find.Name is not None) and Find.Name.startswith('A1.')")
#	query = Query(store, "SELECT *.*")
#	query = Query(store, "SELECT Feature.Name RELATED Feature.~disturbs.Feature WHERE Area.Name == \"A2\"")
	query = Query(store, "SELECT Area.Name, Feature.Name, Find.Name")
#	query = Query(store, "SELECT Area, Feature, Find")
	print()
	print(query.columns)
	print()
#	for row in range(len(query)):
#		print(query[row, "Find.Name"])
#		print([query[row, cls, descr] for cls, descr in query.columns])
#		print(["%s: %s" % (query.columns[col], str(query[row, col])) for col in range(len(query.columns))])
	for row in query:
		print(row)
#	for idx in range(len(query._rows)):
#		print(idx, query._objects[idx].id, query._rows[idx])
	
#	for path in store.get_object_connections(1, 5, {"disturbs","~disturbs"}):
#		print(path)
	
	
	'''
	for path in store.get_class_connections(
		classes = [
#			"*",
			"Area",
			"Feature",
			"Find",
		], 
		relations = [
#			("Feature", "~disturbs", "Feature"),
#			("Feature", "disturbs", "Feature"),
#			("*", "disturbs", "*"),
#			("Feature", "*", "Area"),
#			("Area", "*", "Feature"),
#			("Feature", "~contains", "Area"),
#			("Area", "contains", "Feature"),
		]):
		
#			pass
			print([obj.id for obj in path])
#			print([obj_id for obj_id, classes in path])
	'''
