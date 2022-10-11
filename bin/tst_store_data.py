import deposit
from deposit import __version__
from natsort import natsorted

def get_store_data(store):
	
	def walk(items):
		
		if isinstance(items, list):
			for i in range(len(items)):
				items[i] = walk(items[i])
			return tuple(items)
		elif isinstance(items, dict):
			for key in items:
				items[key] = walk(items[key])
			return tuple(items.items())
		return items
	
	classes = []
	cls_relations = []
	objects = []
	obj_relations = []
	members = []
	metadata = [__version__, store._local_folder, store._max_order]
	
	for cls in store.get_classes():
		classes.append(cls.to_dict())
		for cls2, label in cls.get_relations():
			cls_relations.append((cls.name, label, cls2.name))
		for obj in cls.get_members():
			members.append((cls.name, obj.id))
		for cls2 in cls.get_subclasses():
			members.append((cls.name, cls2.name))
	for obj in store.get_objects():
		objects.append(obj.to_dict())
		for obj2, label in obj.get_relations():
			obj_relations.append((obj.id, label, obj2.id))
	
	for items in [classes, objects, cls_relations, obj_relations, members]:
		items[:] = walk(items)
	
	return tuple([
		tuple(natsorted(metadata)),
		tuple(natsorted(classes)),
		tuple(natsorted(objects)),
		tuple(natsorted(cls_relations)),
		tuple(natsorted(obj_relations)),
		tuple(natsorted(members)),
	])

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
	
	data = get_store_data(store)
	
	print()
	print(data)
	print()
