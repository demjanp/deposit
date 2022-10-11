import deposit
from itertools import combinations
from collections import defaultdict
import numpy as np

if __name__ == "__main__":
	
	store = deposit.Store()
	store.load(path = "c:/data_processed/test_db_large/test_db_large.pickle")
	
	query = store.get_query("SELECT Area WHERE Area.Name == 'A1'")
	for row in query:
		area_id = row[0][0]
		break
	objects = set()
	for obj_feature, label1 in store.get_object(area_id).get_relations():
		if label1 == "contains":
			for find_obj, label2 in obj_feature.get_relations():
				if (label2 == "contains") and find_obj.has_descriptor("Image"):
					objects.add(find_obj)
					print("\robjects: %d             " % (len(objects)), end = "")
	
	combs = list(combinations(objects, 2))
	cmax = len(combs)
	cnt = 0
	for obj1, obj2 in combs:
		if cnt % 1000 == 0:
			print("\r%d/%d            " % (cnt + 1, cmax), end = "")
		cnt += 1
		
		obj1.add_relation(obj2, "diam_dist", weight = round(np.random.random(), 3))
		obj1.add_relation(obj2, "axis_dist", weight = round(np.random.random(), 3))
		obj1.add_relation(obj2, "dice_dist", weight = round(np.random.random(), 3))
		obj1.add_relation(obj2, "dice_rim_dist", weight = round(np.random.random(), 3))
		
		obj2.add_relation(obj1, "diam_dist", weight = round(np.random.random(), 3))
		obj2.add_relation(obj1, "axis_dist", weight = round(np.random.random(), 3))
		obj2.add_relation(obj1, "dice_dist", weight = round(np.random.random(), 3))
		obj2.add_relation(obj1, "dice_rim_dist", weight = round(np.random.random(), 3))
	
	resp = store.save(path = "c:/data_processed/test_db_large/test_db_large_cm.pickle")
