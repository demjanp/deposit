import pytest
import deposit

# Helper functions to create mock classes and objects
def create_mock_class(store, name):
	cls = store.add_class(name)
	return cls

def create_mock_object(store, cls_name, descriptors):
	obj = store.add_object_with_descriptors(store.get_class(cls_name), descriptors)
	return obj

def test_add_single_object_with_descriptors():
	store = deposit.Store()
	data = {("Person", "Name"): "Alice", ("Person", "Age"): 30}
	
	result = store.add_data_row(data)
	
	assert result == 1	# Should add one new object
	assert store.get_class("Person") is not None
	assert len(store.get_objects()) == 1
	obj = next(iter(store.get_objects()))
	assert obj.get_descriptor("Name") == "Alice"
	assert obj.get_descriptor("Age") == 30

def test_add_multiple_objects_with_relations():
	store = deposit.Store()
	data = {
		("Country", "Name"): "Wonderland",
		("City", "Name"): "Fantasytown"
	}
	relations = {("Country", "contains", "City")}
	
	result = store.add_data_row(data, relations)
	
	assert result == 2	# Should add two new objects
	country = next(obj for obj in store.get_objects() if obj.get_descriptor("Name") == "Wonderland")
	city = next(obj for obj in store.get_objects() if obj.get_descriptor("Name") == "Fantasytown")
	assert country.has_relation(city, "contains")

def test_add_unique_class():
	store = deposit.Store()
	data = {("Person", "Name"): "Alice"}
	unique_classes = {"Person"}
	
	result = store.add_data_row(data, unique=unique_classes)
	
	assert result == 1	# Should add one new object
	data["Person", "Name"] = "Alice"  # Adding the same data again
	result = store.add_data_row(data, unique=unique_classes)
	
	assert result == 1	# Should add another new object
	assert len(store.get_objects()) == 2

def test_reuse_existing_object():
	store = deposit.Store()
	data = {("Person", "Name"): "Alice", ("Person", "Age"): 30}
	obj = create_mock_object(store, "Person", {"Name": "Alice"})
	existing = {"Person": obj}
	
	result = store.add_data_row(data, existing=existing)
	
	assert result == 0	# Should reuse the existing object
	assert len(store.get_objects()) == 1
	updated_obj = next(iter(store.get_objects()))
	assert updated_obj.get_descriptor("Age") == 30

def test_return_added_objects():
	store = deposit.Store()
	data = {("Person", "Name"): "Alice", ("City", "Name"): "Fantasytown"}
	relations = {("Person", "lives_in", "City")}
	
	result, added_objects = store.add_data_row(data, relations, return_added=True)
	
	assert result == 2	# Should add two new objects
	assert "Person" in added_objects
	assert "City" in added_objects
	person = added_objects["Person"]
	city = added_objects["City"]
	assert person.get_descriptor("Name") == "Alice"
	assert city.get_descriptor("Name") == "Fantasytown"
	assert person.has_relation(city, "lives_in")

def test_multi_level_relationships():
	store = deposit.Store()
	data = {
		("Person", "Name"): "Alice",
		("City", "Name"): "Fantasytown",
		("District", "Name"): "Wonderland District"
	}
	relations = {
		("Person", "lives_in", "City"),
		("City", "is_in", "District")
	}
	
	result, added_objects = store.add_data_row(data, relations, return_added=True)
	
	assert result == 3	# Should add three new objects
	assert "Person" in added_objects
	assert "City" in added_objects
	assert "District" in added_objects
	
	person = added_objects["Person"]
	city = added_objects["City"]
	district = added_objects["District"]
	
	assert person.get_descriptor("Name") == "Alice"
	assert city.get_descriptor("Name") == "Fantasytown"
	assert district.get_descriptor("Name") == "Wonderland District"
	
	assert person.has_relation(city, "lives_in")
	assert city.has_relation(district, "is_in")



