import unittest

from deposit import (DB, File, Store, Query, DString, DResource, DGeometry)
from rdflib import (Literal, URIRef)
import os
import shutil
import time
from sys import platform

if platform in ["linux", "linux2", "darwin"]:
	os.chdir("/")
	file_root = "/Users/Demi/Desktop/data_test/"
	samples_root = "/Users/Demi/Desktop/_samples/"
else:
	file_root = "data_test/"
	samples_root = "C:/Documents/deposit/_samples/"

#@unittest.skip
class TestStore(unittest.TestCase):
	
	def test_store_main(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		cls_1 = store.queryfnc.get_class_by_label("class 1")
		cls_2 = store.queryfnc.get_class_by_label("class 2")
		self.assertEqual(store.get_dep_class_by_id(obj_0), "Object")
		self.assertEqual(store.get_order(cls_1), 1)
		self.assertEqual(store.get_order(cls_2), 2)
		store.swap_order(cls_1, cls_2)
		self.assertEqual(store.get_order(cls_1), 2)
	
	@unittest.skip
	def test_store_objects(self):

		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		obj_2 = store.add_object_by_name([])
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "descr 1", "value 1")
		self.assertEqual(sorted(store.objects.get().tolist()), [obj_0, obj_1, obj_2])
		self.assertEqual(store.objects.get_classless().tolist(), [obj_2])
		self.assertEqual(store.objects.get_descriptors(obj_0).tolist(), [[descr_rel_0, descr_cls_0]])
		obj_3 = store.add_object_by_name(["class 2"])
		self.assertEqual(sorted(store.objects.get().tolist()), [obj_0, obj_1, obj_2, obj_3])
		store.objects.remove(obj_3)
		self.assertEqual(sorted(store.objects.get().tolist()), [obj_0, obj_1, obj_2])
	
	def test_store_classes(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		cls_1 = store.queryfnc.get_class_by_label("class 1")
		cls_2 = store.queryfnc.get_class_by_label("class 2")
		
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "descr 1", "value 1")
		self.assertTrue(store.classes.is_descriptor(descr_cls_0))
		self.assertEqual(sorted(store.classes.get_descriptors(cls_1)), [descr_cls_0])
		cls_3 = store.classes.add("class 3")
		self.assertEqual(sorted(store.classes.get()), [cls_1, cls_2, descr_cls_0, cls_3])
		store.classes.remove(cls_3)
		self.assertEqual(sorted(store.classes.get()), [cls_1, cls_2, descr_cls_0])
	
	def test_store_members(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		obj_2 = store.add_object_by_name([])
		obj_3 = store.add_object_by_name(["class 2"])
		
		cls_1 = store.queryfnc.get_class_by_label("class 1")
		cls_2 = store.queryfnc.get_class_by_label("class 2")
		
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "descr 1", "value 1")
		cls_3 = store.classes.add("class 3")
		store.members.add(cls_3, obj_2)
		self.assertEqual(sorted(store.members.get(cls_3).tolist()), [obj_2])
		store.members.add(cls_1, cls_3)
		self.assertEqual(store.members.get_parents(obj_2).tolist(), [cls_3])
		self.assertEqual(sorted(store.members.get_all_parents(obj_2).tolist()), [cls_1, cls_3])
		self.assertEqual(store.members.get_subclasses(cls_1).tolist(), [cls_3])
		cls_4 = store.classes.add("class 4")
		store.members.add(cls_3, cls_4)
		self.assertEqual(store.members.get_all_subclasses(cls_1).tolist(), [cls_3, cls_4])
		store.members.remove(cls_3, cls_4)
		self.assertEqual(store.members.get_parents(cls_4).tolist(), [])
	
	@unittest.skip
	def test_store_relations(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "descr 1", "value 1")
		rel_1 = store.relations.add(obj_0, obj_1, "rel 1")
		self.assertEqual(store.relations.get(obj_0, "source").tolist(), [[rel_1, obj_1]])
		self.assertEqual(store.relations.get(obj_1, "target").tolist(), [[rel_1, obj_0]])
		store.relations.remove(rel_1)
		self.assertEqual(store.relations.get(obj_0, "source").tolist(), [])
		descr_2 = store.classes.add("descr 2")
		rel_2 = store.relations.add_descriptor(descr_2, obj_0, "value 2")
		self.assertEqual(sorted(store.objects.get_descriptors(obj_0).tolist()), sorted([[descr_rel_0, descr_cls_0], [rel_2, descr_2]]))
		
	@unittest.skip
	def test_store_geotags(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "descr 1", DResource("file:///%s_samples/sample1.jpg" % samples_root))
		store.geotags.add(descr_rel_0, "POLYGON((100 100, 100 200, 200 200, 200 100))", 1234)
		self.assertEqual(str(store.geotags.get(descr_rel_0)), "<http://www.opengis.net/def/crs/EPSG/0/1234> POLYGON((100 100, 100 200, 200 200, 200 100))")
		tags = store.geotags.get_uri("file:///%s_samples/sample1.jpg" % samples_root) # [[geotag, id_obj, id_rel, id_cls], ...]
		self.assertEqual(len(tags), 1)
		self.assertEqual(str(tags[0][0]), "<http://www.opengis.net/def/crs/EPSG/0/1234> POLYGON((100 100, 100 200, 200 200, 200 100))")
		self.assertEqual(tags[0][1], obj_0)
		self.assertEqual(tags[0][2], descr_rel_0)
		self.assertEqual(tags[0][3], descr_cls_0)
		store.geotags.remove(descr_rel_0)
		self.assertEqual(store.geotags.get(descr_rel_0), None)
	
	@unittest.skip
	def test_store_geometry(self):
	
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		obj_0 = store.add_object_by_name(["class 1"])
		obj_1 = store.add_object_by_name(["class 2"])
		obj_2 = store.add_object_by_name([])
		obj_3 = store.add_object_by_name(["class 2"])
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "geo 1", DGeometry([[100,100],[100,200],[200,200],[200,100]], 1234))
		
		label = store.get_label(descr_rel_0)
		self.assertEqual(str(label), "POLYGON((100 100, 100 200, 200 200, 200 100))")
		self.assertEqual(label.__class__.__name__, "DGeometry")
		self.assertEqual(str(label.label), "<http://www.opengis.net/def/crs/EPSG/0/1234> POLYGON((100 100, 100 200, 200 200, 200 100))")
		self.assertEqual(label.label.__class__.__name__, "Literal")
		self.assertEqual(label.value, "POLYGONZ((100 100 10, 100 200 20, 200 200 30, 200 100 40))")
		self.assertEqual(label.coords, ([[100.0, 100.0, 10.0], [100.0, 200.0, 20.0], [200.0, 200.0, 30.0], [200.0, 100.0, 40.0]], "POLYGONZ"))
		self.assertEqual(label.srid, 1234)
		self.assertEqual(label.working, None)
	
	def test_store_file(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		uri, origname, path = store.file.add_to_store("%ssample1.jpg" % samples_root)
		self.assertEqual(uri, "sample1.jpg")
		path = store.file.get_stored_path(uri)
		self.assertTrue(os.path.isfile(path))
		filename_stored, origname, path = store.file.add_to_store("http://lorempixel.com/output/abstract-q-c-256-128-3.jpg", online = True)
		self.assertEqual(origname, "abstract-q-c-256-128-3.jpg")
		self.assertTrue(os.path.isfile(store.file.get_stored_path(filename_stored)))
		
		self.assertIn(store.file.find_image_format("%ssample1.jpg" % samples_root), ["jpg", "jpeg"])
		self.assertEqual(store.file.find_image_format("%smiska.svg" % samples_root), "svg")
		
		self.assertTrue(os.path.isfile(store.file.get_thumbnail("%ssample1.jpg" % samples_root)))
		self.assertTrue(os.path.isfile(store.file.get_thumbnail(path)))
		
	def test_store_resources(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		path, filename, storage_type = store.resources.get_path("file:///%ssample1.jpg" % samples_root)
		if platform in ["linux", "linux2", "darwin"]:
			self.assertEqual(path, "%ssample1.jpg" % samples_root)
		else:
			self.assertEqual(path, "%ssample1.jpg" % samples_root.replace("/", "\\"))
		self.assertEqual(filename, "sample1.jpg")
		self.assertEqual(storage_type, store.resources.RESOURCE_LOCAL)
		path, filename, storage_type = store.resources.get_path("http://lorempixel.com/output/abstract-q-c-256-128-3.jpg")
		self.assertEqual(path, "http://lorempixel.com/output/abstract-q-c-256-128-3.jpg")
		self.assertEqual(filename, "abstract-q-c-256-128-3.jpg")
		self.assertEqual(storage_type, store.resources.RESOURCE_ONLINE)

		src_path = samples_root
		collect = [] # [[dep_uri, filename, id_rel], ...]
		for name in os.listdir(src_path):
			collect.append([store.resources.add_local("file:///%s" % (os.path.join(src_path, name).replace("\\", "/"))), name, None])
		obj_0 = store.add_object_by_name(["class 1"])
		descr_rel_0, descr_cls_0 = store.add_descriptor_by_name(obj_0, "res 1", collect[0][0])
		collect[0][2] = descr_rel_0
		# TODO implement resources.get
#		self.assertEqual(sorted(store.resources.get().tolist()), sorted(collect))
		path, filename, storage_type = store.resources.get_path(collect[0][0])
		self.assertTrue(os.path.isfile(path))
		self.assertEqual(filename, collect[0][1])
	
	def tearDown(self):
		
		time.sleep(1) # allow all files to close
		if os.path.exists("data_test"):
			shutil.rmtree("data_test")

@unittest.skip
class TestQuery(unittest.TestCase):
	
	def setUp(self):
		
		self.store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		
		obj_0 = self.store.add_object_by_name(["class 1"]) # cls_0
		obj_1 = self.store.add_object_by_name(["class 1"])
		obj_2 = self.store.add_object_by_name(["class 1"])
		
		obj_3 = self.store.add_object_by_name(["class 2"]) # cls_1
		obj_4 = self.store.add_object_by_name(["class 2"])
		obj_5 = self.store.add_object_by_name(["class 2"])
		
		obj_6 = self.store.add_object_by_name(["class 3"]) # cls_2
		obj_7 = self.store.add_object_by_name(["class 3"])
		obj_8 = self.store.add_object_by_name(["class 3"])
		
		obj_9 = self.store.add_object_by_name([]) # classless
		obj_10 = self.store.add_object_by_name([])

		self.store.add_member_by_name("class 4", "class 2") # cls_3
		self.store.add_member_by_name("class 4", "class 3")
		
		self.store.add_descriptor_by_name(obj_0, "descr 1", 1) # cls_4
		self.store.add_descriptor_by_name(obj_0, "descr 2", 2) # cls_5
		self.store.add_descriptor_by_name(obj_0, "descr 3", 3) # cls_6
		self.store.add_descriptor_by_name(obj_6, "descr 4", "four") # cls_7
		
		self.store.relations.add(obj_0, obj_3, "rel 1") # class 1.rel 1.class 2
		self.store.relations.add(obj_1, obj_3, "rel 1") # class 1.rel 1.class 2
		self.store.relations.add(obj_2, obj_3, "rel 1") # class 1.rel 1.class 2
		self.store.relations.add(obj_3, obj_6, "rel 2") # class 2.rel 2.class 3
		self.store.relations.add(obj_0, obj_4, "rel 3") # class 1.rel 3.class 2
		self.store.relations.add(obj_0, obj_9, "rel 1") # class 1.rel 1.[classless]
	
	def doQuery(self, query):
		
		return Query(self.store, query)
	
	def test_query_by_object_id(self):
		
		self.assertEqual(self.doQuery("obj(0)").keys(), ["obj_0"])
		self.assertEqual(self.doQuery("obj(0) or obj(1) or obj(2)").keys(), ["obj_0", "obj_1", "obj_2"])
		self.assertEqual(self.doQuery("class 1 or obj(4)").keys(), ["obj_0", "obj_1", "obj_2", "obj_4"])
		
	def test_query_descriptors(self):
		row = self.doQuery("obj(0).descr 1").items()[0]
		self.assertEqual(row[0], "obj_0")
		self.assertEqual(row[1]["cls_4"].value, "1")
		
		rows = self.doQuery("obj(0).*").items()
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0][1]["cls_4"].value, "1")
		self.assertEqual(rows[0][1]["cls_5"].value, "2")
		self.assertEqual(rows[0][1]["cls_6"].value, "3")
	
	def test_query_traverse_CRCD(self):
		
		self.assertEqual(self.doQuery("class 1.rel 1.class 2").keys(), ["obj_0", "obj_1", "obj_2"])
		self.assertEqual(self.doQuery("class 1.rel 1.class 2.rel 2.class 3").keys(), ["obj_0", "obj_1", "obj_2"])
		
		rows = self.doQuery("class 1.rel 1.class 2.rel 2.class 3.descr 4").items()
		self.assertEqual(len(rows), 3)
		self.assertEqual(rows[0][0], "obj_0")
		self.assertEqual(rows[1][0], "obj_1")
		self.assertEqual(rows[2][0], "obj_2")
		self.assertEqual(rows[0][1]["cls_2.cls_7"].value, "four")
		
		rows = self.doQuery("class 3.~rel 2.class 2.~rel 1.class 1").items()
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0][0], "obj_6")
	
	def test_query_traverse_neg(self):
		
		rows = self.doQuery("!class 1").items()
		for i, id_obj in enumerate(["obj_3", "obj_4", "obj_5", "obj_6", "obj_7", "obj_8"]):
			self.assertEqual(rows[i][0], id_obj)
		rows = self.doQuery("class 1.!rel 1.class 2").items()
		self.assertEqual(rows[0][0], "obj_0")
		rows = self.doQuery("class 2.!~rel 1.class 1").items()
		self.assertEqual(rows[0][0], "obj_4")
	
	def test_query_wildcard(self):
		
		self.assertEqual(self.doQuery("*").keys(), ["obj_0", "obj_1", "obj_2", "obj_3", "obj_4", "obj_5", "obj_6", "obj_7", "obj_8", "obj_9", "obj_10"])
		rows = self.doQuery("class 1.*.class 2").items()
		for i, id_obj in enumerate(["obj_0", "obj_1", "obj_2"]):
			self.assertEqual(rows[i][0], id_obj)
		rows = self.doQuery("class 2.~*.class 1").items()
		for i, id_obj in enumerate(["obj_3", "obj_4"]):
			self.assertEqual(rows[i][0], id_obj)
		self.assertEqual(self.doQuery("class 2.* or class 2").keys(), ["obj_3", "obj_4", "obj_5"])
	
	def test_query_classless_objects(self):
		
		self.assertEqual(self.doQuery("!*").keys(), ["obj_9", "obj_10"])
		self.assertEqual(self.doQuery("class 1.rel 1.!*").keys(), ["obj_0"])
	
	def test_query_subclass(self):
		
		rows = self.doQuery("class 1.rel 1.class 4").items()
		for i, id_obj in enumerate(["obj_0", "obj_1", "obj_2"]):
			self.assertEqual(rows[i][0], id_obj)
		
	def test_query_string_slicing(self):
		
		self.assertEqual(self.doQuery('class 3.descr 4[1] == "o"').keys(), ["obj_6"])
		
	def test_query_operators(self):
		
		self.assertEqual(self.doQuery("class 1.descr 1 < class 1.descr 2").keys(), ["obj_0"])
		self.assertEqual(self.doQuery("class 1.descr 1 + class 1.descr 2 > 2").keys(), ["obj_0"])
		self.assertEqual(self.doQuery("- class 1.descr 1 < 1").keys(), ["obj_0"])
		self.assertEqual(self.doQuery("-class 1.descr 1 < 1").keys(), ["obj_0"])
		query = self.doQuery("((class 1.descr 1 > 0) and (class 1.descr 2 < 3)) or class 3.descr 4")
		self.assertEqual(query.keys(), ["obj_0", "obj_6"])
		self.assertEqual(query["obj_0"]["cls_0.cls_4"].value, "1")
		self.assertEqual(query["obj_0"]["cls_0.cls_5"].value, "2")
		self.assertEqual(query["obj_6"]["cls_2.cls_7"].value, "four")
		self.assertEqual(self.doQuery("*.descr 2 in [2,3]").keys(), ["obj_0"])
	
	def test_query_string_methods(self):
		
		self.assertEqual(self.doQuery("class 3.descr 4.startswith(\"fo\")").keys(), ["obj_6"])
		
	def test_query_quantifiers(self):
		
		store = Store(DB("http://mygraph#", "sqlite://"), File(file_root))
		
		cls_1 = store.classes.add("class 1")
		cls_2 = store.classes.add("class 2")
		cls_3 = store.classes.add("class 3")

		obj_0 = store.add_object_by_name(["class 1"])
		store.add_descriptor_by_name(obj_0, "descr 1", 3)
		store.add_descriptor_by_name(obj_0, "descr 2", 20)
		obj_1 = store.add_object_by_name(["class 1"])
		store.add_descriptor_by_name(obj_1, "descr 1", 11)
		store.add_descriptor_by_name(obj_1, "descr 2", 21)

		obj_2 = store.add_object_by_name(["class 2"])
		store.add_descriptor_by_name(obj_2, "descr 1", 12)
		store.add_descriptor_by_name(obj_2, "descr 2", 22)
		obj_3 = store.add_object_by_name(["class 2"])
		store.add_descriptor_by_name(obj_3, "descr 1", 13)
		store.add_descriptor_by_name(obj_3, "descr 2", 23)
		obj_4 = store.add_object_by_name(["class 2"])
		store.add_descriptor_by_name(obj_4, "descr 1", 14)
		store.add_descriptor_by_name(obj_4, "descr 2", 24)

		obj_5 = store.add_object_by_name(["class 3"])
		store.add_descriptor_by_name(obj_5, "descr 1", 15)
		store.add_descriptor_by_name(obj_5, "descr 2", 25)
		obj_6 = store.add_object_by_name(["class 3"])
		store.add_descriptor_by_name(obj_6, "descr 1", 16)
		store.add_descriptor_by_name(obj_6, "descr 2", 26)
		obj_7 = store.add_object_by_name(["class 3"])
		store.add_descriptor_by_name(obj_7, "descr 1", 17)
		store.add_descriptor_by_name(obj_7, "descr 2", 27)

		store.relations.add(obj_0, obj_2, "rel 1")
		store.relations.add(obj_0, obj_3, "rel 1")
		store.relations.add(obj_0, obj_4, "rel 1")

		store.relations.add(obj_1, obj_2, "rel 1")
		store.relations.add(obj_1, obj_3, "rel 1")
		store.relations.add(obj_1, obj_5, "rel 1")
		store.relations.add(obj_1, obj_6, "rel 1")
		
		query = Query(store, "#(num cls 2, class 1, class 2.~rel 1.obj())")
		self.assertEqual(query.keys(), ["obj_0", "obj_1"])
		self.assertEqual(query["obj_0"]["#num cls 2"].value, "3")
		self.assertEqual(query["obj_1"]["#num cls 2"].value, "2")
		query = Query(store, "#(sum descr 1, class 1, class 2.~rel 1.obj(), descr 1)")
		self.assertEqual(query.keys(), ["obj_0", "obj_1"])
		self.assertEqual(query["obj_0"]["#sum descr 1"].value, "39.0")
		self.assertEqual(query["obj_1"]["#sum descr 1"].value, "25.0")
		query = Query(store, "class 1 and (#(sum descr 1) / 10 > 3) #(sum descr 1, class 1, class 2.~rel 1.obj(), descr 1)")
		self.assertEqual(query.keys(), ["obj_0"])
		
if __name__ == "__main__":
	unittest.main()
