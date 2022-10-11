from collections import defaultdict
from itertools import combinations
import numpy as np
import time

N_PATHS = 20000
LEN_PATH = [3, 7]

def prune_classic(paths):
	
	collect = set()
	paths = sorted(paths, key = lambda row: len(row))
	cmax = len(paths)
	cnt = 1
	for i, path in enumerate(paths):
		if cnt % 1000 == 0:
			print("\rpruning %d/%d           " % (cnt, cmax), end = "")  # DEBUG
		cnt += 1
		path_i = set(paths[i])
		found = False
		for j in range(i+1, len(paths)):
			if path_i.issubset(paths[j]):
				found = True
				break
		if not found:
			collect.add(path)
	
	return collect

def __prune_new(paths):
	
	paths_ = defaultdict(set)
	for path in paths:
		paths_[len(path)].add(path)
	lens = sorted(paths_.keys())[::-1]
	if len(lens) < 2:
		return paths
	
	paths = paths.copy()
	for i in range(len(lens) - 1):
		for path in paths_[lens[i]]:
			for j in range(i + 1, len(lens)):
				for subpath in combinations(path, lens[j]):
					if subpath in paths_[lens[j]]:
						paths_[lens[j]].remove(subpath)
	
	return set.union(*paths_.values())

def __prune_new(paths):
	
	paths_ = defaultdict(list)
	for path in paths:
		paths_[len(path)].append(set(path))
	lens = sorted(paths_.keys())
	if len(lens) < 2:
		return paths
	
	paths = paths.copy()
	for i in range(len(lens) - 1):
		for j in range(i + 1, len(lens)):
			for path_j in paths_[lens[j]]:
				paths_[lens[i]] = [path_i for path_i in paths_[lens[i]] if not path_i.issubset(path_j)]
				if not paths_[lens[i]]:
					break
			if not paths_[lens[i]]:
				break
		if not paths_[lens[i]]:
			continue
	
	return set.union(*[set([tuple(sorted(path)) for path in paths_[key]]) for key in paths_])


def prune_new(paths):
	
	paths_ = defaultdict(list)
	for path in paths:
		paths_[len(path)].append(set(path))
	lens = sorted(paths_.keys())[::-1]
	if len(lens) < 2:
		return paths
	
	paths = paths.copy()
	for i in range(len(lens) - 1):
#		cmax = len(paths_[lens[i]])
#		cnt = 1
		for path_i in paths_[lens[i]]:
#			print("\rprune %d/%d (%d/%d)          " % (i + 1, len(lens) - 1, cnt, cmax), end = "")
#			cnt += 1
			for j in range(i + 1, len(lens)):
				paths_[lens[j]] = [path_j for path_j in paths_[lens[j]] if not path_j < path_i]
#				paths_[lens[j]] = [path_j for path_j in paths_[lens[j]] if len(path_j.intersection(path_i)) < len(path_j)]
	
	return set.union(*[set([tuple(sorted(path)) for path in paths_[key]]) for key in paths_])

def prune_paths(paths):
	
	paths_ = defaultdict(list)
	for path in paths:
		paths_[len(path)].append(set(path))
	lens = sorted(paths_.keys())[::-1]
	if len(lens) < 2:
		return paths
	if min(lens) < 2:
		return paths
	for i in range(len(lens) - 1):
		for path_i in paths_[lens[i]]:
			for j in range(i + 1, len(lens)):
				paths_[lens[j]] = [path_j for path_j in paths_[lens[j]] if not path_j < path_i]
	
	return set.union(*[set([tuple(sorted(path)) for path in paths_[key]]) for key in paths_])

if __name__ == "__main__":
	
	np.random.seed(0)
	
	paths = set()
	while len(paths) < N_PATHS:
		path = np.random.choice(30, np.random.randint(LEN_PATH[0], LEN_PATH[1] + 1), replace = False)
		paths.add(tuple(sorted(path.tolist())))
	
	l0, l1 = np.inf, -np.inf
	for path in paths:
		l0 = min(l0, len(path))
		l1 = max(l1, len(path))
	print()
	print("paths:", len(paths))
	print("len:", l0, l1)
	print()
	
	t0 = time.time()
	paths = prune_paths(paths)
#	paths = prune_classic(paths)
	t1 = time.time() - t0
	
	l0, l1 = np.inf, -np.inf
	for path in paths:
		l0 = min(l0, len(path))
		l1 = max(l1, len(path))
	print()
	print()
	print("pruned:", len(paths))
	print("len:", l0, l1)
	print("time:", t1)
	print()
