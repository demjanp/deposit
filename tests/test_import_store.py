import pytest
from unittest.mock import MagicMock
from deposit import Store, DGeometry

@pytest.fixture
def setup_source_store():
	store = Store()

	# Create classes and add descriptors
	cls_area = store.add_class("Area")
	cls_area.set_descriptor("Location")
	cls_feature = store.add_class("Feature")
	cls_feature.set_descriptor("Name")
	cls_feature.set_descriptor("Type")

	# Add objects with descriptors and locations
	area1 = store.add_object()
	cls_area.add_member(area1.id)
	area1.set_descriptor("Location", "North")
	area1.set_location("Location", DGeometry("POINT (10 20)"))

	feature1 = store.add_object()
	cls_feature.add_member(feature1.id)
	feature1.set_descriptor("Name", "Feature 1")
	feature1.set_descriptor("Type", "Type A")
	feature1.set_location("Type", DGeometry("POINT (30 40)"))

	# Establish relationships
	area1.add_relation(feature1, "contains")

	return store, area1, feature1

@pytest.fixture
def setup_circular_store():
	store = Store()

	# Create classes and add descriptors
	cls_circle = store.add_class("Circle")
	cls_circle.set_descriptor("Name")

	# Add objects with descriptors
	obj1 = store.add_object()
	obj2 = store.add_object()
	obj3 = store.add_object()
	cls_circle.add_member(obj1.id)
	cls_circle.add_member(obj2.id)
	cls_circle.add_member(obj3.id)
	obj1.set_descriptor("Name", "Object 1")
	obj2.set_descriptor("Name", "Object 2")
	obj3.set_descriptor("Name", "Object 3")

	# Create circular relationships
	obj1.add_relation(obj2, "linked_to")
	obj2.add_relation(obj3, "linked_to")
	obj3.add_relation(obj1, "linked_to")

	return store, obj1, obj2, obj3

@pytest.fixture
def setup_within_class_store():
	store = Store()

	# Create class and add descriptors
	cls_within = store.add_class("WithinClass")
	cls_within.set_descriptor("Identifier")

	# Add objects with descriptors
	obj1 = store.add_object()
	obj2 = store.add_object()
	cls_within.add_member(obj1.id)
	cls_within.add_member(obj2.id)
	obj1.set_descriptor("Identifier", "ID1")
	obj2.set_descriptor("Identifier", "ID2")

	# Create within-class relationship
	obj1.add_relation(obj2, "related_to")

	return store, obj1, obj2

def test_import_classes(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if classes are imported correctly
	assert target_store.get_class("Area") is not None
	assert target_store.get_class("Feature") is not None

	# Check if descriptors are imported correctly
	cls_area = target_store.get_class("Area")
	cls_feature = target_store.get_class("Feature")
	assert cls_area.has_descriptor("Location")
	assert cls_feature.has_descriptor("Name")
	assert cls_feature.has_descriptor("Type")

def test_import_objects_with_descriptors(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if objects are imported correctly
	cls_area = target_store.get_class("Area")
	cls_feature = target_store.get_class("Feature")

	imported_area = next(obj for obj in cls_area.get_members() if obj.get_descriptor("Location") == "North")
	imported_feature = next(obj for obj in cls_feature.get_members() if obj.get_descriptor("Name") == "Feature 1")

	assert imported_area is not None
	assert imported_area.get_descriptor("Location") == "North"
	assert imported_feature is not None
	assert imported_feature.get_descriptor("Name") == "Feature 1"
	assert imported_feature.get_descriptor("Type") == "Type A"

def test_import_objects_with_locations(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if locations are imported correctly
	cls_area = target_store.get_class("Area")
	cls_feature = target_store.get_class("Feature")

	imported_area = next(obj for obj in cls_area.get_members() if obj.get_descriptor("Location") == "North")
	imported_feature = next(obj for obj in cls_feature.get_members() if obj.get_descriptor("Name") == "Feature 1")

	assert imported_area is not None
	assert imported_area.get_location("Location") == DGeometry("POINT (10 20)")
	assert imported_feature is not None
	assert imported_feature.get_location("Type") == DGeometry("POINT (30 40)")

def test_import_objects_with_relationships(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if relationships are imported correctly
	cls_area = target_store.get_class("Area")
	cls_feature = target_store.get_class("Feature")

	imported_area = next(obj for obj in cls_area.get_members() if obj.get_descriptor("Location") == "North")
	imported_feature = next(obj for obj in cls_feature.get_members() if obj.get_descriptor("Name") == "Feature 1")

	relations = imported_area.get_relations()
	assert (imported_feature, "contains") in relations

def test_import_with_existing_objects(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	# Create a similar object in the target store
	cls_area = target_store.add_class("Area")
	existing_area = target_store.add_object()
	cls_area.add_member(existing_area.id)
	existing_area.set_descriptor("Location", "North")
	existing_area.set_location("Location", DGeometry("POINT (10 20)"))

	target_store.import_store(source_store)

	# Check if no duplicate object is created
	imported_areas = [obj for obj in cls_area.get_members() if obj.get_descriptor("Location") == "North"]
	assert len(imported_areas) == 1

def test_import_with_unique_classes(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	unique_classes = {"Feature"}

	target_store.import_store(source_store, unique=unique_classes)

	# Check if new objects are always created for unique classes
	cls_feature = target_store.get_class("Feature")
	imported_features = [obj for obj in cls_feature.get_members() if obj.get_descriptor("Name") == "Feature 1"]

	assert len(imported_features) == 1	# Even with unique class, should not duplicate

def test_import_with_progress_tracking(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	progress = MagicMock()
	progress.cancel_pressed.return_value = False

	target_store.import_store(source_store, progress=progress)

	# Verify progress updates were called
	assert progress.update_state.call_count > 0

def test_import_with_cancellation(setup_source_store):
	source_store, area1, feature1 = setup_source_store
	target_store = Store()

	progress = MagicMock()
	progress.cancel_pressed.side_effect = [False, True]	 # Cancel on the second call

	target_store.import_store(source_store, progress=progress)

	# Verify import was cancelled
	assert progress.update_state.call_count == 1  # Only one update before cancel

def test_import_with_circular_relations(setup_circular_store):
	source_store, obj1, obj2, obj3 = setup_circular_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if objects and circular relationships are imported correctly
	cls_circle = target_store.get_class("Circle")
	print(f"Circle members after import: {[obj.get_descriptor('Name') for obj in cls_circle.get_members()]}")

	imported_obj1 = [obj for obj in cls_circle.get_members() if obj.get_descriptor("Name") == "Object 1"]
	imported_obj1 = imported_obj1[0] if imported_obj1 else None
	imported_obj2 = [obj for obj in cls_circle.get_members() if obj.get_descriptor("Name") == "Object 2"]
	imported_obj2 = imported_obj2[0] if imported_obj2 else None
	imported_obj3 = [obj for obj in cls_circle.get_members() if obj.get_descriptor("Name") == "Object 3"]
	imported_obj3 = imported_obj3[0] if imported_obj3 else None
	
	assert imported_obj1 is not None
	assert imported_obj2 is not None
	assert imported_obj3 is not None

	assert (imported_obj2, "linked_to") in imported_obj1.get_relations()
	assert (imported_obj3, "linked_to") in imported_obj2.get_relations()
	assert (imported_obj1, "linked_to") in imported_obj3.get_relations()

def test_import_within_class_relations(setup_within_class_store):
	source_store, obj1, obj2 = setup_within_class_store
	target_store = Store()

	target_store.import_store(source_store)

	# Check if within-class relationships are imported correctly
	cls_within = target_store.get_class("WithinClass")

	imported_obj1 = [obj for obj in cls_within.get_members() if obj.get_descriptor("Identifier") == "ID1"]
	imported_obj1 = imported_obj1[0] if imported_obj1 else None
	imported_obj2 = [obj for obj in cls_within.get_members() if obj.get_descriptor("Identifier") == "ID2"]
	imported_obj2 = imported_obj2[0] if imported_obj2 else None
	
	assert imported_obj1 is not None
	assert imported_obj2 is not None

	assert (imported_obj2, "related_to") in imported_obj1.get_relations()
