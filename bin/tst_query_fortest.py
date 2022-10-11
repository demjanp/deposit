#!/usr/bin/env python
# -*- coding: utf-8 -*-

import deposit

import os
import shutil
from natsort import natsorted

if __name__ == "__main__":
	
	store = deposit.Store()
	
	finds = store.add_class("Find")
	features = store.add_class("Feature")
	weird = store.add_class(";Weird.Cls, SELECT")
	areas = store.add_class("Area")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	fe11.set_descriptor("Area", 2)
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	fe12.set_descriptor("Area", 3)
	fe13 = features.add_member()
	fe13.set_descriptor("Name", "A1.F3")
	fe24 = features.add_member()
	fe24.set_descriptor("Name", "A2.F4")
	fe24.set_descriptor("Area", 4)
	fe25 = features.add_member()
	fe25.set_descriptor("Name", "A2.F5")
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	f111.set_descriptor("Material", "Bone")
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	f112.set_descriptor("Material", "Ceramics")
	f113 = finds.add_member()
	f113.set_descriptor("Name", "A1.F1.3")
	f113.set_descriptor("Material", "Ceramics")
	f121 = finds.add_member()
	f121.set_descriptor("Name", "A1.F2.1")
	f121.set_descriptor("Material", "Bronze")
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
	fe11.add_relation(f113, "contains")
	fe12.add_relation(f121, "contains")
	fe12.add_relation(f122, "contains")
	fe13.add_relation(f131, "contains")
	fe24.add_relation(f241, "contains")
	
	fe11.add_relation(fe12, "disturbs")
	fe11.add_relation(fe13, "covers")
	fe24.add_relation(fe25, "disturbs")
	
	w1 = weird.add_member()
	w1.set_descriptor(";Weird.Descr, SELECT", "WA1")
	w2 = weird.add_member()
	w2.set_descriptor(";Weird.Descr, SELECT", "WB1")
	w3 = weird.add_member()
	w3.set_descriptor(";Weird.Descr, SELECT", "WB2")
	
	w2.add_relation(w3, "weird rel, WHERE")
	
	obj = store.add_object()
	obj.set_descriptor("Name", "Classless 1")
	obj = store.add_object()
	obj.set_descriptor("Name", 2)
	
#	print("FINDS", f111.id, f112.id, f113.id, f121.id, f122.id, f131.id, f241.id)
	
	for querystr, expected in [
#		["SELECT Area, Feature.Name", [[(1, None), (3, 'A1.F1')], [(1, None), (4, 'A1.F2')], [(1, None), (5, 'A1.F3')], [(2, None), (6, 'A2.F4')], [(2, None), (7, 'A2.F5')]]],
		["SELECT Area.*, Feature.*, Find.*", [[(1, 'A1'), (3, 2), (3, 'A1.F1'), (8, 'A1.F1.1'), (8, 'Bone')], [(1, 'A1'), (3, 2), (3, 'A1.F1'), (9, 'A1.F1.2'), (9, 'Ceramics')], [(1, 'A1'), (3, 2), (3, 'A1.F1'), (10, 'A1.F1.3'), (10, 'Ceramics')], [(1, 'A1'), (4, 3), (4, 'A1.F2'), (11, 'A1.F2.1'), (11, 'Bronze')], [(1, 'A1'), (4, 3), (4, 'A1.F2'), (12, 'A1.F2.2'), (12, None)], [(1, 'A1'), (5, None), (5, 'A1.F3'), (13, 'A1.F3.1'), (13, None)], [(2, 'A2'), (6, 4), (6, 'A2.F4'), (14, 'A2.F4.1'), (14, None)], [(2, 'A2'), (7, None), (7, 'A2.F5'), (14, 'A2.F4.1'), (14, None)]]],
#		["SELECT Area.Name, Feature.Name, COUNT(Find) AS [Cnt Find] WHERE Find is not None GROUP BY Area.Name, Feature.Name", [[(1, 'A1'), (3, 'A1.F1'), (None, 3)], [(1, 'A1'), (4, 'A1.F2'), (None, 2)], [(1, 'A1'), (5, 'A1.F3'), (None, 1)], [(2, 'A2'), (6, 'A2.F4'), (None, 1)], [(2, 'A2'), (7, 'A2.F5'), (None, 1)]]],
#		["SELECT Area.Name, SUM(Feature.Area) AS [SUM Area] GROUP BY Area.Name", [[(1, 'A1'), (None, 5.0)], [(2, 'A2'), (None, 4.0)]]],
#		["SELECT Area.Name, Feature.Name, Find.Name WHERE Find is not None", [[(1, 'A1'), (3, 'A1.F1'), (8, 'A1.F1.1')], [(1, 'A1'), (3, 'A1.F1'), (9, 'A1.F1.2')], [(1, 'A1'), (3, 'A1.F1'), (10, 'A1.F1.3')], [(1, 'A1'), (4, 'A1.F2'), (11, 'A1.F2.1')], [(1, 'A1'), (4, 'A1.F2'), (12, 'A1.F2.2')], [(1, 'A1'), (5, 'A1.F3'), (13, 'A1.F3.1')], [(2, 'A2'), (6, 'A2.F4'), (14, 'A2.F4.1')], [(2, 'A2'), (7, 'A2.F5'), (14, 'A2.F4.1')]]],
#		["SELECT [;Weird.Cls, SELECT].[;Weird.Descr, SELECT] WHERE [;Weird.Cls, SELECT].[;Weird.Descr, SELECT].startswith('WB')", [[(16, 'WB1')], [(17, 'WB2')]]],
#		["SELECT Feature.Name RELATED Feature.disturbs.Feature", [[(3, 'A1.F1')], [(4, 'A1.F2')], [(6, 'A2.F4')], [(7, 'A2.F5')]]],
#		["SELECT Feature.Name RELATED OBJ(3).disturbs.Feature", [[(3, 'A1.F1')], [(4, 'A1.F2')]]],
#		["SELECT Feature.Name RELATED OBJ(3).*.Feature", [[(3, 'A1.F1')], [(4, 'A1.F2')], [(5, 'A1.F3')]]],
#		["SELECT Find.Name, Feature.Name RELATED OBJ(3).contains.Find", [[(8, 'A1.F1.1'), (3, 'A1.F1')], [(9, 'A1.F1.2'), (3, 'A1.F1')], [(10, 'A1.F1.3'), (3, 'A1.F1')]]],
#		["SELECT [;Weird.Cls, SELECT].* RELATED [;Weird.Cls, SELECT].[weird rel, WHERE].[;Weird.Cls, SELECT]", [[(16, 'WB1')], [(17, 'WB2')]]],
#		["SELECT Find.*", [[(8, 'A1.F1.1'), (8, 'Bone')], [(9, 'A1.F1.2'), (9, 'Ceramics')], [(10, 'A1.F1.3'), (10, 'Ceramics')], [(11, 'A1.F2.1'), (11, 'Bronze')], [(12, 'A1.F2.2'), (12, None)], [(13, 'A1.F3.1'), (13, None)], [(14, 'A2.F4.1'), (14, None)]]],
#		["SELECT !*", [[(18, None)], [(19, None)]]],
#		["SELECT !*.*", [[(18, 'Classless 1')], [(19, 2)]]],
#		["SELECT !*.Name WHERE isinstance(!*.Name, str) and !*.Name.startswith('Class')", [[(18, 'Classless 1')]]],
	]:
		query = store.get_query(querystr)
#		print("\"%s\"" % querystr)
#		print(query.columns)
#		rows = natsorted([row for row in query])
		rows = [row for row in query]
#		expected = natsorted(expected)
#		if rows != expected:
		if True:
			print("\n\n")
			print("\"%s\"" % querystr)
			print(query.columns)
			print("....")
#			print([row for row in rows])
			for row in rows:
				print(row)
			print("--->")
#			print(expected)
			for row in expected:
				print(row)
			print()
