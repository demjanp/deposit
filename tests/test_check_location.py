import pytest
from deposit import Store, DGeometry

@pytest.fixture
def setup_store_with_locations():
    store = Store()

    # Create classes
    cls_area = store.add_class("Area")
    cls_feature = store.add_class("Feature")
    cls_find = store.add_class("Find")

    # Add objects to classes and set descriptors
    area1 = store.add_object()
    cls_area.add_member(area1.id)
    area1.set_descriptor("Name", "Area 1")

    area2 = store.add_object()
    cls_area.add_member(area2.id)
    area2.set_descriptor("Name", "Area 2")

    feature1 = store.add_object()
    cls_feature.add_member(feature1.id)
    feature1.set_descriptor("Name", "Feature 1")
    feature1.set_descriptor("Type", "Type A")
    feature1.set_descriptor("Position", "Position 1")  # Ensure descriptor before location
    feature1.set_location("Type", DGeometry("POINT (10 20)"))
    feature1.set_location("Position", DGeometry("POINT (15 25)"))

    feature2 = store.add_object()
    cls_feature.add_member(feature2.id)
    feature2.set_descriptor("Name", "Feature 2")
    feature2.set_descriptor("Type", "Type B")
    feature2.set_location("Type", DGeometry("POINT (30 40)"))

    find1 = store.add_object()
    cls_find.add_member(find1.id)
    find1.set_descriptor("Name", "Find 1")
    find1.set_descriptor("Material", "Stone")

    find2 = store.add_object()
    cls_find.add_member(find2.id)
    find2.set_descriptor("Name", "Find 2")
    find2.set_descriptor("Material", "Metal")

    # Establish relationships
    area1.add_relation(feature1, "contains")
    area1.add_relation(feature2, "contains")
    feature1.add_relation(find1, "contains")
    feature2.add_relation(find2, "contains")

    return store, area1, feature1, feature2, find1, find2

def test_find_object_by_class(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations

    cls_area = store.get_class("Area")
    cls_feature = store.get_class("Feature")

    obj = store.find_object_with_descriptors([cls_area], {"Name": "Area 1"})
    assert obj is not None
    assert obj.get_descriptor("Name") == "Area 1"

    obj = store.find_object_with_descriptors([cls_feature], {"Name": "Feature 1"})
    assert obj is not None
    assert obj.get_descriptor("Name") == "Feature 1"

def test_find_object_by_descriptor(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_find = store.get_class("Find")

    obj = store.find_object_with_descriptors([cls_find], {"Material": "Metal"})
    assert obj is not None
    assert obj.get_descriptor("Material") == "Metal"

    obj = store.find_object_with_descriptors([cls_find], {"Material": "Stone"})
    assert obj is not None
    assert obj.get_descriptor("Material") == "Stone"

def test_find_object_with_missing_descriptor(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_feature = store.get_class("Feature")

    obj = store.find_object_with_descriptors([cls_feature], {"Type": "Type C"})
    assert obj is None

def test_find_object_by_location(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_feature = store.get_class("Feature")

    obj = store.find_object_with_descriptors([cls_feature], {"Type": "Type A"}, {"Type": DGeometry("POINT (10 20)")})
    assert obj is not None
    assert obj.get_descriptor("Type") == "Type A"
    assert obj.get_location("Type") == DGeometry("POINT (10 20)")

def test_find_object_by_related_data(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_area = store.get_class("Area")

    related_data = {("Area", "contains", "Feature", "Name"): "Feature 2"}

    obj = store.find_object_with_descriptors([cls_area], {"Name": "Area 1"}, related_data=related_data)
    assert obj is not None
    assert obj.get_descriptor("Name") == "Area 1"

def test_find_object_with_nested_related_data(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_feature = store.get_class("Feature")

    related_data = {("Feature", "contains", "Find", "Material"): "Metal"}

    obj = store.find_object_with_descriptors([cls_feature], {"Name": "Feature 2"}, related_data=related_data)
    assert obj is not None
    assert obj.get_descriptor("Name") == "Feature 2"

    # Validate the relationship
    find2 = [member for member in store.get_class("Find").get_members() if member.get_descriptor("Name") == "Find 2"][0]
    assert find2 in [rel[0] for rel in obj.get_relations() if rel[1] == "contains"]

def test_find_object_with_multiple_criteria(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_feature = store.get_class("Feature")

    related_data = {("Feature", "contains", "Find", "Material"): "Stone"}

    obj = store.find_object_with_descriptors(
        [cls_feature],
        {"Name": "Feature 1", "Type": "Type A"},
        {"Type": DGeometry("POINT (10 20)")},
        related_data
    )
    assert obj is not None
    assert obj.get_descriptor("Name") == "Feature 1"
    assert obj.get_descriptor("Type") == "Type A"
    assert obj.get_location("Type") == DGeometry("POINT (10 20)")

def test_find_object_with_multiple_related_data(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_area = store.get_class("Area")

    related_data = {
        ("Area", "contains", "Feature", "Name"): "Feature 2",
        ("Feature", "contains", "Find", "Material"): "Metal"
    }

    obj = store.find_object_with_descriptors([cls_area], {"Name": "Area 1"}, related_data=related_data)
    assert obj is not None
    assert obj.get_descriptor("Name") == "Area 1"

    # Validate the relationships
    feature2 = [member for member in store.get_class("Feature").get_members() if member.get_descriptor("Name") == "Feature 2"][0]
    find2 = [member for member in store.get_class("Find").get_members() if member.get_descriptor("Material") == "Metal"][0]

    assert feature2 in [rel[0] for rel in obj.get_relations() if rel[1] == "contains"]
    assert find2 in [rel[0] for rel in feature2.get_relations() if rel[1] == "contains"]

def test_find_object_no_match(setup_store_with_locations):
    store, area1, feature1, feature2, find1, find2 = setup_store_with_locations
    cls_area = store.get_class("Area")

    obj = store.find_object_with_descriptors([cls_area], {"Name": "Nonexistent Area"})
    assert obj is None
