import pytest
from deposit.store.dobject import DObject
from deposit import Store

@pytest.fixture(scope='module')
def store():
	yield Store()

def test_get_subgraph_basic(store):
	# Create objects and relations
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	obj4 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	obj4.set_descriptor("TestDescriptor", "obj4")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	obj3.add_relation(obj4, "rel3")
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	# Map original object descriptors to subgraph objects
	obj1_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj3"), None)
	obj4_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj4"), None)

	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is not None
	assert obj4_sub is not None

def test_get_subgraph_including_related_objects(store):
	# Create objects and relations
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	# Map original object descriptors to subgraph objects
	obj1_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj3"), None)

	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is not None


def test_get_subgraph_within_class_relations(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	
	# Add classes
	cls = store.add_class("TestClass")
	cls.add_member(obj1.id)
	cls.add_member(obj2.id)
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	# Map original object descriptors to subgraph objects
	obj1_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj3"), None)
	
	# obj2 should not be included because it is of the same class as obj1
	assert obj1_sub is not None
	assert obj2_sub is None	 # This is correct based on the rules
	assert obj3_sub is None	 # obj3 should not be included because it is only reachable through obj2


def test_get_subgraph_empty_graph(store):
	# Clear previous data
	store.clear()
	obj = store.add_object()
	obj.set_descriptor("TestDescriptor", "obj")
	subgraph_store = store.get_subgraph([obj])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	obj_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj"), None)

	assert obj_sub is not None
	assert len(subgraph_objects) == 1

def test_get_subgraph_no_neighbors(store):
	# Clear previous data
	store.clear()
	obj = store.add_object()
	obj.set_descriptor("TestDescriptor", "obj")
	subgraph_store = store.get_subgraph([obj])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	obj_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj"), None)

	assert obj_sub is not None
	assert len(subgraph_objects) == 1

def test_get_subgraph_invalid_object(store):
	# Clear previous data
	store.clear()
	invalid_obj = DObject(store, -1)
	
	with pytest.raises(Exception):
		store.get_subgraph([invalid_obj])

def test_get_subgraph_complex_relations(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	# Map original object descriptors to subgraph objects
	obj1_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((obj for obj in subgraph_objects if obj.get_descriptor("TestDescriptor") == "obj3"), None)

	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is not None

def test_get_subgraph_single_node(store):
	# Clear previous data
	store.clear()
	obj = store.add_object()
	obj.set_descriptor("TestDescriptor", "single_node")
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj])
	
	subgraph_objects = list(subgraph_store.get_objects())
	obj_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "single_node"), None)
	
	assert obj_sub is not None
	assert len(subgraph_objects) == 1

def test_get_subgraph_cyclic_graph(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	obj3.add_relation(obj1, "rel3")	 # Creating a cycle
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	obj1_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj3"), None)
	
	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is not None
	assert len(subgraph_objects) == 3

def test_get_subgraph_large_depth(store):
	# Clear previous data
	store.clear()
	obj_list = [store.add_object() for _ in range(10)]
	
	for i, obj in enumerate(obj_list):
		obj.set_descriptor("TestDescriptor", f"obj{i+1}")
		if i > 0:
			obj_list[i-1].add_relation(obj, "rel")
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj_list[0]])
	
	subgraph_objects = list(subgraph_store.get_objects())
	subgraph_ids = [obj.get_descriptor("TestDescriptor") for obj in subgraph_objects]
	
	assert len(subgraph_objects) == 10
	for i in range(10):
		assert f"obj{i+1}" in subgraph_ids

def test_get_subgraph_multiple_classes(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	
	cls1 = store.add_class("Class1")
	cls2 = store.add_class("Class2")
	
	cls1.add_member(obj1.id)
	cls1.add_member(obj2.id)
	cls2.add_member(obj2.id)
	
	# Get subgraph
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	obj1_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj3"), None)
	
	# obj2 should be excluded due to class membership with obj1
	assert obj1_sub is not None
	assert obj2_sub is None
	assert obj3_sub is None	 # obj3 should also be excluded as it's indirectly connected through obj2

def test_get_subgraph_self_referencing_node(store):
    # Clear previous data
    store.clear()
    obj = store.add_object()
    obj.set_descriptor("TestDescriptor", "self_node")
    obj.add_relation(obj, "self_rel")
    
    # Get subgraph
    subgraph_store = store.get_subgraph([obj])
    
    subgraph_objects = list(subgraph_store.get_objects())
    obj_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "self_node"), None)
    
    assert obj_sub is not None
    assert len(subgraph_objects) == 1
    # Convert generator to list for comparison
    relations = list(obj_sub.get_relations())
    expected_relations = [(obj_sub, "self_rel"), (obj_sub, "~self_rel")]

    # Sort the lists to avoid order issues
    assert sorted(relations) == sorted(expected_relations)

def test_get_subgraph_empty_input(store):
	# Clear previous data
	store.clear()
	
	# Get subgraph with empty input list
	subgraph_store = store.get_subgraph([])
	
	subgraph_objects = list(subgraph_store.get_objects())
	
	assert len(subgraph_objects) == 0

def test_get_subgraph_multiple_entry_points(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	obj4 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	obj4.set_descriptor("TestDescriptor", "obj4")
	
	obj1.add_relation(obj2, "rel1")
	obj2.add_relation(obj3, "rel2")
	obj3.add_relation(obj4, "rel3")
	
	# Get subgraph with multiple entry points
	subgraph_store = store.get_subgraph([obj1, obj3])
	
	subgraph_objects = list(subgraph_store.get_objects())
	obj1_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj3"), None)
	obj4_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj4"), None)
	
	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is not None
	assert obj4_sub is not None

def test_get_subgraph_disconnected_graph(store):
	# Clear previous data
	store.clear()
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	obj4 = store.add_object()
	
	obj1.set_descriptor("TestDescriptor", "obj1")
	obj2.set_descriptor("TestDescriptor", "obj2")
	obj3.set_descriptor("TestDescriptor", "obj3")
	obj4.set_descriptor("TestDescriptor", "obj4")
	
	obj1.add_relation(obj2, "rel1")
	# obj3 and obj4 are disconnected from obj1 and obj2
	
	# Get subgraph from obj1
	subgraph_store = store.get_subgraph([obj1])
	
	subgraph_objects = list(subgraph_store.get_objects())
	obj1_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj1"), None)
	obj2_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj2"), None)
	obj3_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj3"), None)
	obj4_sub = next((o for o in subgraph_objects if o.get_descriptor("TestDescriptor") == "obj4"), None)
	
	assert obj1_sub is not None
	assert obj2_sub is not None
	assert obj3_sub is None
	assert obj4_sub is None
