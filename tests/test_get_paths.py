import unittest
from deposit import Store
from deposit.utils.fnc_get_linked_objects import (get_paths)

class TestGetPathsFunction(unittest.TestCase):

	def setUp(self):
		# Setup a basic store with some objects and relationships
		self.store = Store()
		self.obj1 = self.store.add_object()
		self.obj2 = self.store.add_object()
		self.obj3 = self.store.add_object()
		self.obj4 = self.store.add_object()
		self.cls1 = self.store.add_class("Class1")
		self.cls2 = self.store.add_class("Class2")
		self.cls3 = self.store.add_class("Class3")
		self.cls1.add_member(self.obj1.id)
		self.cls1.add_member(self.obj2.id)
		self.cls2.add_member(self.obj3.id)
		self.cls3.add_member(self.obj4.id)
		self.obj1.add_relation(self.obj2, "related_to")
		self.obj2.add_relation(self.obj3, "connected_to")
		self.obj3.add_relation(self.obj4, "connected_to")
	
	def test_basic_path_retrieval(self):
		# Test basic path retrieval between obj2 and obj3
		cls_lookup = {self.obj2.id: {"Class1"}, self.obj3.id: {"Class2"}, self.obj4.id: {"Class3"}}
		paths = get_paths(self.store, self.obj2.id, cls_lookup, {}, {}, {}, ["Class1", "Class2", "Class3"], set(), set())
		self.assertIn((self.obj2.id, self.obj3.id, self.obj4.id), paths)
		
	def test_no_circular_paths(self):
		# Test that circular paths are not included
		self.obj3.add_relation(self.obj1, "loops_to")
		cls_lookup = {self.obj1.id: {"Class1"}, self.obj2.id: {"Class1"}, self.obj3.id: {"Class2"}}
		paths = get_paths(self.store, self.obj1.id, cls_lookup, {}, {}, {}, ["Class1", "Class2"], set(), set())
		self.assertNotIn((self.obj1.id, self.obj2.id, self.obj3.id, self.obj1.id), paths)

	def test_mandatory_class_inclusion(self):
		# Test that paths include mandatory classes
		cls_lookup = {self.obj1.id: {"Class1"}, self.obj2.id: {"Class1"}, self.obj3.id: {"Class2"}}
		mandatory_classes = {"Class1"}
		paths = get_paths(self.store, self.obj1.id, cls_lookup, {}, {}, {}, ["Class1", "Class2"], set(), mandatory_classes)
		self.assertTrue(all(any(cls in cls_lookup[obj] for obj in path) for path in paths for cls in mandatory_classes))
	
	def test_within_class_relations(self):
		# Test paths that should respect within-class relationships
		cls_lookup = {self.obj1.id: {"Class1"}, self.obj2.id: {"Class1"}, self.obj3.id: {"Class2"}}
		within_cls_rels = {"Class1": {"related_to"}}
		paths = get_paths(self.store, self.obj1.id, cls_lookup, {}, within_cls_rels, {}, ["Class1", "Class2"], set(), set())
		self.assertIn((self.obj1.id, self.obj2.id), paths)
	
	def test_asterisk_relations(self):
		# Test that asterisk relations are considered
		cls_lookup = {self.obj1.id: {"Class1"}, self.obj2.id: {"Class1"}, self.obj3.id: {"Class2"}}
		asterisk_rels = {("Class1", "Class2")}
		paths = get_paths(self.store, self.obj1.id, cls_lookup, {}, {}, asterisk_rels, ["Class1", "Class2"], set(), set())
		self.assertTrue(any(cls_lookup[obj] for obj in path if path[-1] in cls_lookup and cls_lookup[path[-1]] == "Class2") for path in paths)
	
	def test_connecting_objects(self):
		# Test paths with objects connecting between specified classes
		connecting = {self.obj3.id}
		cls_lookup = {self.obj2.id: {"Class1"}, self.obj4.id: {"Class3"}}
		paths = get_paths(self.store, self.obj2.id, cls_lookup, {}, {}, {}, ["Class1", "Class3"], connecting, set())
		self.assertIn((self.obj2.id, self.obj4.id), paths)
	
	def test_edge_case_no_objects(self):
		# Test with no objects in the graph
		cls_lookup = {}
		paths = get_paths(self.store, 0, cls_lookup, {}, {}, {}, ["Class1", "Class2"], set(), set())
		self.assertEqual(paths, set())



if __name__ == "__main__":
	unittest.main()
