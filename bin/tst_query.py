#!/usr/bin/env python
# -*- coding: utf-8 -*-

import deposit

import os
import shutil

if __name__ == "__main__":
	
	store = deposit.Store()
	
	local_folder = "test_db"
	if os.path.isdir(local_folder):
		shutil.rmtree(local_folder)
	store.set_local_folder(local_folder)
	
	# for i in range(30): # 1 - 30
	# 	store.add_object()
	
	finds = store.add_class("Find")
	features = store.add_class("Feature")
#	features = store.add_class("Feature, X")
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
	f111.set_resource_descriptor("Image", "samples\\ščščťť.jpg", is_stored = False)
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	f112.set_resource_descriptor("Image", "samples\\image1.jpg")
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
	
	obj = store.add_object()
	obj.set_descriptor("Name", "CLSL1")
	
#	print("fe11", fe11.id)
#	print("fe12", fe12.id)
#	print("fe24", fe24.id)
#	print("fe25", fe25.id)
	
#	store.add_relation(2, 3, "disturbs")
#	store.add_relation(4, 3, "disturbs")
	
#	query = store.get_query("SELECT Area, Feature, COUNT(Find) AS [Cnt Find] WHERE Find is not None GROUP BY Area, Feature")
#	query = store.get_query("SELECT Area, Feature, Find WHERE Find is not None")
#	query = store.get_query("SELECT Area, Feature, Find")
#	query = store.get_query("SELECT Area, Feature, COUNT(Find) AS Cnt_Find GROUP BY Area, Feature")
#	query = store.get_query("SELECT Area.Name, Feature.Name, Find.Name WHERE (Area is not None) and (Find.Name is not None) and Find.Name.startswith('A1.F1.')")
#	query = store.get_query("SELECT Area.Name, Feature.Name WHERE (Find.Name is not None) and Find.Name.startswith('A1.')")
	query = store.get_query("SELECT !*")
#	query = store.get_query("SELECT !*.Name")
#	query = store.get_query("SELECT !*.*")
#	query = store.get_query("SELECT Feature.Name RELATED Feature.~disturbs.Feature WHERE Area.Name == \"A2\"")
#	query = store.get_query("SELECT Feature.Name, Find.Name RELATED Feature.~disturbs.Feature WHERE Find is not None")
#	query = store.get_query("SELECT Area.Name, Feature.Name, Find.Name, Find.Image")
#	query = store.get_query("SELECT Area.Name, [Feature, X].Name, Find.Name")
#	query = store.get_query("SELECT Find.*")
#	query = store.get_query("SELECT Area.*, Feature, Find")
#	query = store.get_query("SELECT Area.*, Feature.*, Find.*")
#	query = store.get_query("SELECT Area.*, Feature.*")
#	query = store.get_query("SELECT Feature.*")
#	query = store.get_query("SELECT Area.*, Find.Name RELATED Area.contains.Find")
#	query = store.get_query("SELECT [Feature, X].*, Find.Name RELATED [Feature, X].disturbs.[Feature, X] WHERE [Feature, X].Name == 'A2.F4'")
#	query = store.get_query("SELECT Area.*, [Feature, X].*")
#	query = store.get_query("SELECT Area, Feature, Find WHERE Area == 1")
#	query = store.get_query("SELECT OBJ(1).*, Feature.* RELATED OBJ(1).contains.Feature")
#	query = store.get_query("SELECT OBJ(1).*, Feature.*")
#	query = store.get_query("SELECT [Area].*")
#	query = store.get_query("SELECT *.Name")
#	query = store.get_query("SELECT OBJ(1,2) WHERE OBJ(1,2).Name == 'A1'")
#	query = store.get_query("SELECT OBJ(1).Name, [Feature, X].Name")
#	query = store.get_query("SELECT OBJ(3).*, Feature.Name RELATED OBJ(3).disturbs.Feature")
#	query = store.get_query("SELECT Feature.* RELATED OBJ(1).contains.Feature")
#	query = store.get_query("SELECT [Feature, X].* RELATED [Feature, X].~disturbs.OBJ(3,6)")  # Feature.disturbs.fe11
#	query = store.get_query("SELECT [Feature, X].* RELATED [Feature, X].~disturbs.[Feature, X]")  # Feature.disturbs.fe11
#	query = store.get_query("SELECT [Feature, X].Name, Find.Name RELATED OBJ(3).contains.Find WHERE Find is not None")
#	query = store.get_query("SELECT Find.Name RELATED OBJ(3).contains.Find WHERE Find is not None")
	print()
	print(query.columns)
	print()
#	for row in range(len(query)):
#		res = query[row, "Find.Image"][1]
#		print(res, res.__class__.__name__)
#	 	print(query[row, "Find.Name"])
	# 	print([query[row, cls, descr] for cls, descr in query.columns])
	# 	print(["%s: %s" % (query.columns[col], str(query[row, col])) for col in range(len(query.columns))])
	for row in query:
		print(row)
	# for idx in range(len(query._rows)):
	# 	print(idx, query._objects[idx].id, query._rows[idx])
	
	# for path in store.get_object_connections(1, 5, {"disturbs","~disturbs"}):
	# 	print(path)
	
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
