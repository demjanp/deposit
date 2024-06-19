# Helper functions for Store.get_linked_objects

from collections import defaultdict
from itertools import product
import copy

def get_linked_objects(store, classes, relations, progress=None):
	# classes = [class_name, ...]
	# relations = [(class1, label, class2), ...]
	
	rels = defaultdict(set)	 # {(class1, class2): set(label, ...), ...}
	within_cls_rels = defaultdict(set)	# {class: set(label, ...), ...}
	asterisk_rels = set()  # set((class1, class2), ...)
	mandatory_classes = set()  # set(class, ...)

	for cls1, lbl, cls2 in relations:
		if isinstance(cls1, tuple):
			mandatory_classes.add(cls1[0])
		if isinstance(cls2, tuple):
			mandatory_classes.add(cls2[0])
		if lbl == "*":
			asterisk_rels.add((cls1, cls2))
			asterisk_rels.add((cls2, cls1))
		clss = get_within_class_rel(store, cls1, cls2)
		if clss:
			within_cls_rels[cls1].add(lbl)
		else:
			rels[(cls1, cls2)].add(lbl)
			rels[(cls2, cls1)].add(store.reverse_relation(lbl))
	
	cls0 = classes[0]
	objects0 = get_class_members(store, cls0)
	if not objects0:
		# no objects found in the first specified class
		return set()
	
	cls_lookup = defaultdict(set)
	collect = []
	for cls in classes:
		if isinstance(cls, tuple):
			mandatory_classes.add(cls[0])
		objs = objects0 if (cls == cls0) else get_class_members(store, cls)
		if objs and not cls_is_objs(cls):
			collect.append(cls)
			for obj_id in objs:
				cls_lookup[obj_id].add(cls)
	classes = collect
	
	if (len(classes) == 1) and (classes[0] not in within_cls_rels):
		# only one class and no within-class relations apply
		return set([(obj_id,) for obj_id in objects0])

	connecting = set()
	cls0_ = get_class_members(store, cls0, leave_names=True)
	if len(classes) > 1:
		# collect objects from unspecified classes at shortest paths between specified classes
		for cls1 in classes[1:]:
			if (cls0, cls1) in rels:
				continue
			cls1_ = get_class_members(store, cls1, leave_names=True)
			connecting.update(store.G.shortest_path_between_classes(cls0_, cls1_))
		connecting = connecting.difference(classes)
		if connecting:
			connecting = set.union(*[get_class_members(store, cls) for cls in connecting])
	
	paths = set()
	cmax = len(objects0)
	cnt = 1
	if progress is not None:
		progress.update_state(value=0, maximum=cmax)
	for obj_id0 in objects0:
		if (progress is not None) and (cnt % 100 == 0):
			if progress.cancel_pressed():
				return set()
			progress.update_state(value=cnt)
		cnt += 1
		paths_ = get_paths(store,
			obj_id0, cls_lookup, rels, within_cls_rels,
			asterisk_rels, classes, connecting, mandatory_classes
		)
		if paths_:
			paths.update(paths_)

	if progress is not None:
		progress.update_state(value=cmax)
	
	return paths

def cls_is_objs(class_name):
	if isinstance(class_name, str):
		return False
	if not isinstance(class_name, tuple):
		raise Exception("Unexpected Class name: %s" % (str(class_name)))
	for c_ in list(class_name):
		if not isinstance(c_, int):
			raise Exception("Unexpected Class name: %s" % (str(class_name)))
	return True

def get_class_members(store, class_name, leave_names=False):
	if class_name == "*":
		return set([obj.id for obj in store.get_objects()])
	if class_name == "!*":
		return set([obj.id for obj in store.get_objects() if not obj.has_class()])
	if cls_is_objs(class_name):
		return set(list(class_name))
	cls = store.get_class(class_name)
	if cls is None:
		return set()
	if leave_names:
		return class_name
	return set([obj.id for obj in cls.get_members()])

def get_class_names(store, cls):
	if cls == "*":
		return set([cls_.name for cls_ in store.get_classes()])
	if cls == "!*":
		return set(["!*"])
	if isinstance(cls, tuple):
		clss = set.union(*[set([cls_.name for cls_ in \
			store.get_object(obj_id).get_classes()]) for \
				obj_id in list(cls)])
		if not clss:
			clss = set(["!*"])
		return clss
	return set([cls])

def get_within_class_rel(store, cls1, cls2):
	clss1 = get_class_names(store, cls1)
	clss2 = get_class_names(store, cls2)
	return clss1.intersection(clss2)

def get_paths(store, obj_id0, cls_lookup, rels, within_cls_rels, asterisk_rels, classes, connecting, mandatory_classes):
	"""
	Get all paths from obj_id0 to objects from specified classes.
	Rule 1. If classes or relations contains object specifications OBJ(1, ...)
	require each path to contain one of those objects
	Rule 2. If a cls1.*.cls2 relation is specified, the path must contain an 
	edge between cls1 and cls2.
	Rule 3. The paths cannot have within-class edges unless explicitly
	specified in relations.
	Rule 4. If a path contains an edge between classes as specified in 
	relations, it must have a label as specified in relations.
	"""
	if obj_id0 not in cls_lookup or not cls_lookup:
		return set()

	queue = [[[obj_id0], set(), cls_lookup[obj_id0].copy(), False, False]]
	done = set()
	skip = set()

	while queue:
		path, found_asterisk, found_classes, rule1, rule3 = queue.pop()
		found_next = False
		if not mandatory_classes:
			rule1 = True
		if (len(found_classes) < len(classes)) or within_cls_rels:
			src = path[-1]
			clss_src = cls_lookup.get(src, None)
			src_within_cls_rels = get_within_class_relations(clss_src, within_cls_rels)
			
			if check_rule1(clss_src, mandatory_classes):
				rule1 = True
			
			for tgt, label in store.G.iter_object_relations(src):
				if skip_tgt(skip, tgt, path):
					continue
				
				clss_tgt = cls_lookup.get(tgt, None)
				if skip_unrelated_objects(clss_tgt, tgt, connecting):
					continue
				
				clss = collect_class_combinations(clss_src, clss_tgt, rels, asterisk_rels)
				
				# Avoid paths with invalid within-class relations
				if clss_tgt and found_classes.intersection(clss_tgt):
					if (not within_cls_rels) and (not (src_within_cls_rels and (label in src_within_cls_rels or '*' in src_within_cls_rels) and clss_tgt & clss_src)):
						continue
				
				# Directly add paths with valid within-class relations
				found_classes_ = found_classes.copy()
				if (clss_src and clss_tgt) and clss_src.intersection(clss_tgt):
					if label in set.union(*list(within_cls_rels.get(class_name, set()) for class_name in clss_src)):
						found_classes_.update(clss_tgt)
						add_valid_path(done, path + [tgt], cls_lookup)
						continue
				
				found_asterisk, rule3 = process_rules(store, rule1, rule3, clss, clss_tgt, clss_src, within_cls_rels,
													  rels, asterisk_rels, label, found_asterisk, src_within_cls_rels, found_classes_)
				
				if rule1 and (found_classes_ or clss_tgt):
					update_found_classes(found_classes_, clss_tgt)
				
				queue.append([path + [tgt], found_asterisk.copy(), found_classes_, rule1, rule3])
				found_next = True

		if found_next:
			continue
		if check_final_rules(found_asterisk, asterisk_rels, rule3, within_cls_rels, rule1, mandatory_classes):
			add_valid_path(done, path, cls_lookup)

	return done

def get_within_class_relations(clss_src, within_cls_rels):
	if clss_src:
		common = clss_src.intersection(within_cls_rels.keys())
		if common:
			return within_cls_rels[common.pop()]
	return None

def check_rule1(clss_src, mandatory_classes):
	return clss_src and clss_src.intersection(mandatory_classes)

def skip_tgt(skip, tgt, path):
	if tgt in skip:
		return True
	skip.add(tgt)
	return tgt in path

def skip_unrelated_objects(clss_tgt, tgt, connecting):
	return (clss_tgt is None) and (tgt not in connecting)

def collect_class_combinations(clss_src, clss_tgt, rels, asterisk_rels):
	if clss_src and clss_tgt:
		if rels or asterisk_rels:
			return list(product(clss_src, clss_tgt))
	return []

def process_rules(store, rule1, rule3, clss, clss_tgt, clss_src, within_cls_rels,
				  rels, asterisk_rels, label, found_asterisk, src_within_cls_rels, found_classes):
	if clss and asterisk_rels:
		for cls_src, cls_tgt in clss:
			if (cls_src, cls_tgt) in asterisk_rels:
				found_asterisk.add((cls_src, cls_tgt))

	if clss_tgt:
		common = found_classes.intersection(clss_tgt)
		if common:
			if not rule3 and clss_src:
				rule3 = check_within_class_relations(clss_src, within_cls_rels, label)
			if not valid_within_class_relation(src_within_cls_rels, label, clss_tgt, clss_src):
				return found_asterisk, rule3

	rule4_valid = validate_rule4(clss, store, rels, label)
	if not rule4_valid:
		return found_asterisk, rule3

	return found_asterisk, rule3

def check_within_class_relations(clss_src, within_cls_rels, label):
	for cls in clss_src:
		if cls in within_cls_rels and within_cls_rels[cls].intersection([label, "*"]):
			return True
	return False

def valid_within_class_relation(src_within_cls_rels, label, clss_tgt, clss_src):
	return src_within_cls_rels and ((label in src_within_cls_rels) or ('*' in src_within_cls_rels)) and clss_tgt.intersection(clss_src)

def validate_rule4(clss, store, rels, label):
	if clss:
		for cls_src, cls_tgt in clss:
			if (cls_src, cls_tgt) in rels:
				if not (rels[(cls_src, cls_tgt)].intersection([label, "*"])):
					return False
			elif (cls_tgt, cls_src) in rels:
				if not (rels[(cls_tgt, cls_src)].intersection([store.reverse_relation(label), "*"])):
					return False
			else:
				return False
	return True

def update_found_classes(found_classes, clss_tgt):
	if clss_tgt:
		found_classes.update(clss_tgt)

def check_final_rules(found_asterisk, asterisk_rels, rule3, within_cls_rels, rule1, mandatory_classes):
	if not all_rule2_valid(found_asterisk, asterisk_rels):
		return False
	if within_cls_rels and not rule3:
		return False
	if mandatory_classes and not rule1:
		return False
	return True

def all_rule2_valid(found_asterisk, asterisk_rels):
	for cls1, cls2 in asterisk_rels:
		if not (((cls1, cls2) in found_asterisk) or ((cls2, cls1) in found_asterisk)):
			return False
	return True

def add_valid_path(done, path, cls_lookup):
	done.add(tuple(sorted([obj_id for obj_id in path if obj_id in cls_lookup])))

def all_within_class_relations_satisfied(found_classes, classes):
	"""
	Check if all specified within-class relations are satisfied.
	"""
	return all(cls in found_classes for cls in classes)
