import pytest
import deposit

from deposit import __version__
from deposit.utils.fnc_files import (url_to_path, as_url)
from deposit.utils.fnc_serialize import (value_to_str)

import deposit

from collections import defaultdict
from natsort import natsorted
import datetime
import psycopg2
import shutil
import os
import re

def set_resource(obj, n):
	path = pytest.resources[n][0]
	obj.set_resource_descriptor("Resource", path)
	pytest.names_resources[obj.get_descriptor("Name")] = n

def get_objects_with_resources(store):
	
	objects_with_resources = {}
	for obj in store.get_objects():
		name = obj.get_descriptor("Name")
		if name is None:
			continue
		res = obj.get_descriptor("Resource")
		if not isinstance(res, deposit.DResource):
			continue
		objects_with_resources[pytest.names_resources[name]] = obj
	return objects_with_resources

def dict_to_nested_tuples(d):
	result = []
	for key, value in d.items():
		if isinstance(value, dict):
			value = dict_to_nested_tuples(value)
		result.append((key, value))
	result = sorted(result)
	return tuple(result)

def obj_to_dict(obj):
	
	data = obj.to_dict()
	if "descriptors" in data:
		for name in data["descriptors"]:
			if not isinstance(data["descriptors"][name], dict):
				continue
			if data["descriptors"][name]['dtype'] == 'DResource':
				data["descriptors"][name]['objects'] = []
				(url, filename, is_stored, is_image) = data["descriptors"][name]['value']
				data["descriptors"][name]['value'] = (None, filename, is_stored, is_image)
	return data

def get_structure(store):
	
	structure = {}
	
	structure["objects"] = []
	for obj in store.get_objects():
		row = {}
		row["descriptors"] = dict_to_nested_tuples(obj_to_dict(obj))
		row["related"] = defaultdict(list)
		for obj2, label in obj.get_relations():
			row["related"][label].append(dict_to_nested_tuples(obj_to_dict(obj2)))
		for label in row["related"]:
			row["related"][label] = sorted(row["related"][label])
		row["related"] = dict_to_nested_tuples(row["related"])
		structure["objects"].append(dict_to_nested_tuples(row))
	structure["objects"] = sorted(structure["objects"])
	
	structure["classes"] = {}
	for cls in store.get_classes():
		structure["classes"][cls.name] = {}
		structure["classes"][cls.name]["descriptors"] = sorted(cls.get_descriptor_names())
		structure["classes"][cls.name]["related"] = defaultdict(list)
		for cls2, label in cls.get_relations():
			structure["classes"][cls.name]["related"][label].append(cls2.name)
		structure["classes"][cls.name]["related"] = dict(structure["classes"][cls.name]["related"])
		for label in structure["classes"][cls.name]["related"]:
			structure["classes"][cls.name]["related"][label] = sorted(structure["classes"][cls.name]["related"][label])
		structure["classes"][cls.name]["related"] = dict_to_nested_tuples(structure["classes"][cls.name]["related"])
	
	return dict_to_nested_tuples(structure)

@pytest.fixture(scope='session', autouse=True)
def setup():
	
	pytest.local_folder = "tests\\test db with spaces"
	pytest.resources = [
		("https://picsum.photos/200", "200.jpeg", "200.jpeg", True, True),
		("tests\\samples dir with spaces\\!@#$%^&() .xx.yy.zz", "__________.xx.yy.zz", "!@#$%^&() .xx.yy.zz", True, False),
		("tests\\samples dir with spaces\\image1.jpg", "image1.jpg", "image1.jpg", True, True),
		("tests\\samples dir with spaces\\image2.jpg", "image2.jpg", "image2.jpg", True, True),
		("tests\\samples dir with spaces\\noext", "noext", "noext", True, False),
		("tests\\samples dir with spaces\\test_pdf_1.pdf", "test_pdf_1.pdf", "test_pdf_1.pdf", True, False),
		("tests\\samples dir with spaces\\test_pdf_2.pdf", "test_pdf_2.pdf", "test_pdf_2.pdf", True, False),
		("tests\\samples dir with spaces\\ščščťť.šľš", "scsctt.sls", "ščščťť.šľš", True, False),
	]
	pytest.names_resources = {}

	store = deposit.Store()
	if os.path.isdir(pytest.local_folder):
		shutil.rmtree(pytest.local_folder)
	store.set_local_folder(pytest.local_folder)
	
	# Setting up classes and their members as described in the provided code
	finds = store.add_class("Find")
	features = store.add_class("Feature")
	areas = store.add_class("Area")
	sites = store.add_class("Site")
	
	s1 = sites.add_member()
	s1.set_descriptor("Name", "S1")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	set_resource(fe11, 0)
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	set_resource(fe12, 1)
	fe13 = features.add_member()
	fe13.set_descriptor("Name", "A1.F3")
	fe14 = features.add_member()
	fe14.set_descriptor("Name", "A1.F4")
	fe24 = features.add_member()
	fe24.set_descriptor("Name", "A2.F4")
	set_resource(fe24, 2)
	fe25 = features.add_member()
	fe25.set_descriptor("Name", "A2.F5")
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	set_resource(f111, 3)
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	set_resource(f112, 4)
	f113 = finds.add_member()
	f113.set_descriptor("Name", "A1.F1.3")
	set_resource(f113, 5)
	f121 = finds.add_member()
	f121.set_descriptor("Name", "A1.F2.1")
	set_resource(f121, 6)
	f122 = finds.add_member()
	f122.set_descriptor("Name", "A1.F2.2")
	set_resource(f122, 7)
	f131 = finds.add_member()
	f131.set_descriptor("Name", "A1.F3.1")
	f241 = finds.add_member()
	f241.set_descriptor("Name", "A2.F4.1")
	
	s1.add_relation(a1, "contains")
	s1.add_relation(a2, "contains")
	
	a1.add_relation(fe11, "contains")
	a1.add_relation(fe12, "contains")
	a1.add_relation(fe13, "contains")
	a1.add_relation(fe14, "contains")
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
	fe12.add_relation(fe14, "disturbs")
	fe11.add_relation(fe13, "covers")
	fe13.add_relation(fe14, "covers")
	fe14.add_relation(fe11, "covers")
	fe24.add_relation(fe25, "disturbs")
	
	store.save(path = os.path.join(pytest.local_folder, "data.pickle"))
	
	yield
	
	# cleanup
	if os.path.isdir(pytest.local_folder):
		shutil.rmtree(pytest.local_folder)

def test_added_resources():
	
	store = deposit.Store()
	store.load(path=os.path.join(pytest.local_folder, "data.pickle"))
	
	objects_with_resources = get_objects_with_resources(store)
	
	for n in objects_with_resources:
		_, exp_stored, exp_filename, exp_is_stored, exp_is_image = pytest.resources[n]
		res = objects_with_resources[n].get_descriptor("Resource")
		url, filename, is_stored, is_image = res.value
		assert os.path.isfile(url_to_path(url)) == True
		assert os.path.split(url)[-1] == exp_stored
		assert exp_filename == filename
		assert exp_is_stored == is_stored
		assert exp_is_image == is_image

def test_import():
	
	tgt_store = deposit.Store()
	
	tgt_local_folder = "tests\\tgt_db"
	if os.path.isdir(tgt_local_folder):
		shutil.rmtree(tgt_local_folder)
	os.mkdir(tgt_local_folder)
	
	tgt_store.set_local_folder(tgt_local_folder)
	
	# Setting up classes and their members as described in the provided code
	finds = tgt_store.add_class("Find")
	features = tgt_store.add_class("Feature")
	areas = tgt_store.add_class("Area")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	fe24 = features.add_member()
	fe24.set_descriptor("Name", "A2.F4")
	fe25 = features.add_member()
	fe25.set_descriptor("Name", "A2.F5")
	
	a1.add_relation(fe11, "contains")
	a1.add_relation(fe12, "contains")
	a2.add_relation(fe24, "contains")
	a2.add_relation(fe25, "contains")
	
	src_store = deposit.Store()
	src_store.load(path=os.path.join(pytest.local_folder, "data.pickle"))
	
	tgt_store.import_store(src_store)
	tgt_store.save(path=os.path.join(tgt_local_folder, "data.pickle"))
	assert get_structure(tgt_store) == get_structure(src_store)
	
	found_resources = {}
	for obj in tgt_store.get_objects():
		name = obj.get_descriptor("Name")
		if name is None:
			continue
		res = obj.get_descriptor("Resource")
		if not isinstance(res, deposit.DResource):
			continue
		found_resources[name] = res
	for name in pytest.names_resources:
		n = pytest.names_resources[name]
		_, exp_stored, exp_filename, exp_is_stored, exp_is_image = pytest.resources[n]
		url, filename, is_stored, is_image = found_resources[name].value
		assert name in found_resources
		assert as_url(tgt_local_folder) == os.path.split(os.path.split(url)[0])[0]
		assert os.path.isfile(url_to_path(url)) == True
		assert os.path.split(url)[-1] == exp_stored
		assert exp_filename == filename
		assert exp_is_stored == is_stored
		assert exp_is_image == is_image
	
	shutil.rmtree(tgt_local_folder)
	
def test_export():
	
	src_store = deposit.Store()
	src_store.load(path=os.path.join(pytest.local_folder, "data.pickle"))
	
	tgt_local_folder = "tests\\tgt_db"
	if os.path.isdir(tgt_local_folder):
		shutil.rmtree(tgt_local_folder)
	os.mkdir(tgt_local_folder)
	
	feature = src_store.get_class("Feature")
	fe11 = src_store.find_object_with_descriptors([feature], {"Name": "A1.F1"})
	fe12 = src_store.find_object_with_descriptors([feature], {"Name": "A1.F2"})
	
	tgt_store = src_store.get_subgraph([fe11, fe12])
	tgt_store.save(path=os.path.join(tgt_local_folder, "data.pickle"))
	
	# Set up a reference store to check tgt_store
	ref_store = deposit.Store()

	# Setting up classes and their members as described in the provided code
	finds = ref_store.add_class("Find")
	features = ref_store.add_class("Feature")
	areas = ref_store.add_class("Area")
	sites = ref_store.add_class("Site")
	
	s1 = sites.add_member()
	s1.set_descriptor("Name", "S1")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	set_resource(fe11, 0)
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	set_resource(fe12, 1)
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	set_resource(f111, 3)
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	set_resource(f112, 4)
	f113 = finds.add_member()
	f113.set_descriptor("Name", "A1.F1.3")
	set_resource(f113, 5)
	f121 = finds.add_member()
	f121.set_descriptor("Name", "A1.F2.1")
	set_resource(f121, 6)
	f122 = finds.add_member()
	f122.set_descriptor("Name", "A1.F2.2")
	set_resource(f122, 7)
	
	s1.add_relation(a1, "contains")
	s1.add_relation(a2, "contains")
	
	a1.add_relation(fe11, "contains")
	a1.add_relation(fe12, "contains")
	
	fe11.add_relation(f111, "contains")
	fe11.add_relation(f112, "contains")
	fe11.add_relation(f113, "contains")
	fe12.add_relation(f121, "contains")
	fe12.add_relation(f122, "contains")
	
	fe11.add_relation(fe12, "disturbs")
	
	assert get_structure(tgt_store) == get_structure(ref_store)
	
	if os.path.isdir(tgt_local_folder):
		shutil.rmtree(tgt_local_folder)

