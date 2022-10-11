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
	f241.set_descriptor("Dict", {"area": "A2", "feature": "F4", "find": 1})
	
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
	
	fe11.add_relation(fe12, "disturbs", weight = 0.123)
	fe24.add_relation(fe25, "disturbs", weight = 0.456)
	
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
	
	resp = store.save(path = "test_db/temp_w.json")
	print("saved:", resp)
	
