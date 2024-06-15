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


def test_repeating_values():
	
	store = deposit.Store()
	relations = {('Area', 'contains', 'Feature'), ('Feature', 'contains', 'Sample')}
	data_rows = [
		{('Area', 'Name'): 1, ('Feature', 'Name'): 1, ('Sample', 'Id'): 1},
		{('Area', 'Name'): 1, ('Feature', 'Name'): 2, ('Sample', 'Id'): 1},
		{('Area', 'Name'): 1, ('Feature', 'Name'): 3, ('Sample', 'Id'): 1},
		{('Area', 'Name'): 2, ('Feature', 'Name'): 1, ('Sample', 'Id'): 1},
		{('Area', 'Name'): 2, ('Feature', 'Name'): 1, ('Sample', 'Id'): 2},
		{('Area', 'Name'): 2, ('Feature', 'Name'): 1, ('Sample', 'Id'): 3},
		{('Area', 'Name'): 3, ('Feature', 'Name'): 1, ('Sample', 'Id'): 1},
		{('Area', 'Name'): 3, ('Feature', 'Name'): 2, ('Sample', 'Id'): 1},
	]
	for data in data_rows:
		store.add_data_row(data, relations)
	
	for data in data_rows:
		vals = [data[('Area', 'Name')], data[('Feature', 'Name')], data[('Sample', 'Id')]]
		value = "_".join([str(val) for val in vals])
		data[("Sample", "Note")] = value
		store.add_data_row(data, relations)
	
	query = store.get_query("SELECT Area.Name, Feature.Name, Sample.Id, Sample.Note")
	for row in query:
		print(row)
		vals = [row[0][1], row[1][1], row[2][1]]
		assert row[3][1] == "_".join([str(val) for val in vals])

def test_exact_match():
	
	store = deposit.Store()
	data_rows_1 = [
		{('Sample', 'A'): 1, ('Sample', 'B'): 1, ('Sample', 'C'): 1},
		{('Sample', 'A'): None, ('Sample', 'B'): 1, ('Sample', 'C'): 1},
		{('Sample', 'A'): 1, ('Sample', 'B'): 1, ('Sample', 'C'): None},
	]
	for data in data_rows_1:
		store.add_data_row(data, exact_match=False)
	query = store.get_query("SELECT Sample.A, Sample.B, Sample.C")
	assert len(query) == 1
	for row in query:
		assert row == [(1, 1), (1, 1), (1, 1)]
	
	data_rows_2 = [
		{('Sample', 'A'): None, ('Sample', 'B'): 1, ('Sample', 'C'): None},
		{('Sample', 'A'): 1, ('Sample', 'B'): None, ('Sample', 'C'): 1},
		{('Sample', 'A'): None, ('Sample', 'B'): None, ('Sample', 'C'): 1},
		{('Sample', 'A'): 1, ('Sample', 'B'): None, ('Sample', 'C'): None},
	]
	for data in data_rows_2:
		store.add_data_row(data, exact_match=False)
	query = store.get_query("SELECT Sample.A, Sample.B, Sample.C")
	assert len(query) == 1
	for row in query:
		assert row == [(1, 1), (1, 1), (1, 1)]
	
	store.clear()
	for data in data_rows_1:
		store.add_data_row(data, exact_match=True)
	for data in data_rows_2:
		store.add_data_row(data, exact_match=True)
	query = store.get_query("SELECT Sample.A, Sample.B, Sample.C")
	assert [row for row in query] == [
		[(1, 1), (1, 1), (1, 1)],
		[(2, None), (2, 1), (2, 1)],
		[(3, 1), (3, 1), (3, None)],
		[(4, None), (4, 1), (4, None)],
		[(5, 1), (5, None), (5, 1)],
		[(6, None), (6, None), (6, 1)],
		[(7, 1), (7, None), (7, None)],
	]
	
	data_rows_3 = [
		{('Sample', 'Id'): 3, ('Sample', 'A'): 1, ('Sample', 'B'): 1, ('Sample', 'C'): None},
		{('Sample', 'Id'): 6, ('Sample', 'A'): None, ('Sample', 'B'): None, ('Sample', 'C'): 1},
		{('Sample', 'Id'): 1, ('Sample', 'A'): 1, ('Sample', 'B'): 1, ('Sample', 'C'): 1},
		{('Sample', 'Id'): 2, ('Sample', 'A'): None, ('Sample', 'B'): 1, ('Sample', 'C'): 1},
		{('Sample', 'Id'): 5, ('Sample', 'A'): 1, ('Sample', 'B'): None, ('Sample', 'C'): 1},
		{('Sample', 'Id'): 4, ('Sample', 'A'): None, ('Sample', 'B'): 1, ('Sample', 'C'): None},
		{('Sample', 'Id'): 7, ('Sample', 'A'): 1, ('Sample', 'B'): None, ('Sample', 'C'): None},
	]
	check_rows = {}
	for data in data_rows_3:
		check_rows[data[('Sample', 'Id')]] = [data[('Sample', 'A')], data[('Sample', 'B')], data[('Sample', 'C')]]
		store.add_data_row(data, exact_match=False)
	query = store.get_query("SELECT Sample.Id, Sample.A, Sample.B, Sample.C")
	for row in query:
		assert check_rows[row[0][1]] == [row[1][1], row[2][1], row[3][1]]
	
