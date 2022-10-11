import deposit
from itertools import combinations
from collections import defaultdict
import numpy as np
import os

N_AREAS = 5
N_FEATURES = 1000
N_STRAT = 500
N_FINDS = 20
N_IMAGES = 1100

'''
N_AREAS = 5
N_FEATURES = 100
N_STRAT = 50
N_FINDS = 20
N_IMAGES = 1100
'''

'''
N_AREAS = 2
N_FEATURES = 10
N_STRAT = 10
N_FINDS = 5
N_IMAGES = 5
'''

if __name__ == "__main__":
	
	img_folder = "c:/data_processed/sample_images"
	image_pool = []
	for fname in os.listdir(img_folder):
		image_pool.append(os.path.join(img_folder, fname))
	
	store = deposit.Store()
	store.set_local_folder("c:/data_processed/test_db_medium/")
	
	cls_area = store.add_class("Area")
	cls_feature = store.add_class("Feature")
	cls_find = store.add_class("Find")
	
	for i in range(N_AREAS):
		area_name = "A%d" % (i + 1)
		obj_area = cls_area.add_member()
		obj_area.set_descriptor("Name", area_name)
		
		features = []
		for j in range(N_FEATURES):
			feature_name = "%s.F%d" % (area_name, j + 1)
			obj_feature = cls_feature.add_member()
			obj_feature.set_descriptor("Name", feature_name)
			obj_area.add_relation(obj_feature, "contains")
			features.append([obj_feature, feature_name])
		
		cnt = 0
		while cnt < N_STRAT:
			j = np.random.randint(N_FEATURES)
			k0 = j + 1
			k1 = N_FEATURES
			if k0 >= k1:
				continue
			k = np.random.randint(k0, k1)
			features[j][0].add_relation(features[k][0], "cut_by")
			cnt += 1
		
		finds = []
		n_finds = defaultdict(int)
		cnt = 0
		while cnt < N_FEATURES * N_FINDS:
			j = np.random.randint(N_FEATURES)
			k = n_finds[j]
			find_name = "%s.N%d" % (features[j][1], k + 1)
			obj_find = cls_find.add_member()
			obj_find.set_descriptor("Name", find_name)
			features[j][0].add_relation(obj_find, "contains")
			finds.append([obj_find, find_name])
			n_finds[j] += 1
			cnt += 1
		
		cnt = 1
		for j in np.random.choice(len(finds), N_IMAGES, replace = False):
			print("\rArea %d/%d Image %d/%d            " % (i + 1, N_AREAS, cnt, N_IMAGES), end = "")
			cnt += 1
			finds[j][0].set_resource_descriptor("Image", np.random.choice(image_pool), filename = "%s.jpg" % (finds[j][1].replace(".", "_")))
		
#	resp = store.save(path = "c:/data_processed/test_db_medium/test_db_medium.pickle")
	resp = store.save(path = "c:/data_processed/test_db_large/test_db_large.pickle")
