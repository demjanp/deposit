#!/usr/bin/env python

import deposit

import time

if __name__ == "__main__":

	res = deposit.DResource()
	geo = deposit.DGeometry()
	dat = deposit.DDateTime()
	print(res, geo, dat)
	
	store = deposit.Store()
	
	obj1 = store.add_object()  # 1
	obj2 = store.add_object()  # 2
	obj3 = store.add_object()  # 3
	obj4 = store.add_object()  # 4
	obj5 = store.add_object()  # 5
	obj6 = store.add_object()  # 6
	obj7 = store.add_object()  # 7
	obj8 = store.add_object()  # 8
	
	clsB = store.add_class("Cls B")
	clsA = store.add_class("Cls A")
	clsC = store.add_class("Cls C")
	
	store.switch_order(clsA, clsB)
	
	clsA.add_member(obj1)
	clsA.add_member(obj2.id)
	clsA.add_member(obj3)
	
	clsB.add_member(obj2)
	clsB.add_member(obj4)
	clsB.add_member(obj5)
	clsB.add_member(obj6)
	
	clsC.add_member(obj7)
	clsC.add_member(obj8)
	
	obj1.set_descriptor("D1", 1)
	obj2.set_descriptor("D1", 2)
	obj3.set_descriptor("D1", 3)
	
	clsA.set_descriptor("DA")
	clsB.set_descriptor("DB")
	
	clsAB = store.add_class("Cls AB")
	clsAB.add_subclass(clsA)
	
	print()
	print(clsA)
	print(clsAB.get_subclasses())
	print()
	raise
	
	clsAB.add_subclass(clsB.name)
	clsB.add_subclass(clsC)
	
	obj1.add_relation(obj2, "relA", 0.1)
	print(sorted(list(store.get_relation_labels())))
	obj1.add_relation(obj2, "relB")
	obj1.add_relation(obj3, "relA", 0.2)
	
	obj2.del_relation(obj1, "~relA")
	
	clsA.add_relation(clsB, "crelA")
	clsA.add_relation(clsC, "crelA")
	
	clsB.del_relation(clsA, "~crelA")
	
	print(sorted(list(store.get_relation_labels())))
	
#	obj1.rename_rescriptor("D1", "DX1")
	store.get_class("D1").rename("DX1")
	
#	for obj in [obj1, obj2, obj3]:
#		for name in obj.get_descriptor_names():
#			print(obj.id, name, obj.get_descriptor(name))
