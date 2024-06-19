import pytest
from deposit import Store

def setup_store():
    # Create a store and populate it with classes and objects
    store = Store()

    # Create classes
    cls_area = store.add_class("Area")
    cls_feature = store.add_class("Feature")
    cls_find = store.add_class("Find")

    # Add objects to classes
    area1 = store.add_object()
    cls_area.add_member(area1.id)
    area1.set_descriptor("Name", "Area 1")

    feature1 = store.add_object()
    cls_feature.add_member(feature1.id)
    feature1.set_descriptor("Name", "Feature 1")
    feature1.set_descriptor("Type", "Type A")

    feature2 = store.add_object()
    cls_feature.add_member(feature2.id)
    feature2.set_descriptor("Name", "Feature 2")
    feature2.set_descriptor("Type", "Type B")

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

def test_basic_relationship_check():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {("Area", "contains", "Feature", "Name"): "Feature 1"}
    n_found = store._check_related(area1, related_data)
    assert n_found == 1

def test_nested_relationship_check():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {("Feature", "contains", "Find", "Material"): "Stone"}
    n_found = store._check_related(feature1, related_data)
    assert n_found == 1

def test_missing_relationship():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {("Feature", "contains", "Find", "Material"): "Gold"}
    n_found = store._check_related(feature1, related_data)
    assert n_found == -1

def test_cyclic_relationship_handling():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    # Introduce a cyclic relationship
    find1.add_relation(feature1, "contained_in")

    related_data = {("Feature", "contains", "Find", "Material"): "Stone"}
    n_found = store._check_related(feature1, related_data)
    assert n_found == 1

def test_empty_related_data():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {}
    assert store._check_related(area1, related_data) == 0
    assert store._check_related(feature1, related_data) == 0
    assert store._check_related(find1, related_data) == 0

def test_invalid_class_or_descriptor():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {("Area", "contains", "Feature", "Type"): "Type C"}
    n_found = store._check_related(area1, related_data)
    assert n_found == -1

    related_data = {("Area", "contains", "InvalidClass", "Name"): "Feature 1"}
    n_found = store._check_related(area1, related_data)
    assert n_found == -1

def test_complex_relationship_check():
    store, area1, feature1, feature2, find1, find2 = setup_store()

    related_data = {
        ("Area", "contains", "Feature", "Name"): "Feature 1",
        ("Feature", "contains", "Find", "Material"): "Stone"
    }
    n_found = store._check_related(area1, related_data)
    assert n_found == 2
