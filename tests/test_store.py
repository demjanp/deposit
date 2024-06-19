#!/usr/bin/env python

import pytest

from deposit.datasource.db import DB
from deposit.datasource.db_rel import DBRel

from deposit import __version__
from deposit.utils.fnc_files import (url_to_path)
from deposit.utils.fnc_serialize import (value_to_str)
from deposit.store.dresource import DResource

import deposit

from natsort import natsorted
import datetime
import psycopg2
import shutil
import os
import re

@pytest.fixture(scope='module')
def store():
	
	yield deposit.Store()

def test_add_object(store):
	
	pytest.obj1 = store.add_object()
	pytest.obj2 = store.add_object()
	pytest.obj3 = store.add_object()
	pytest.obj4 = store.add_object()
	
	assert store.get_objects() == set([pytest.obj1, pytest.obj2, pytest.obj3, pytest.obj4])

def test_delete_object(store):
	
	store.del_object(pytest.obj2)
	
	assert store.get_objects() == set([pytest.obj1, pytest.obj3, pytest.obj4])
	
	pytest.obj2 = store.add_object()
	
	assert store.get_objects() == set([pytest.obj1, pytest.obj2, pytest.obj3, pytest.obj4])

def test_add_class(store):
	
	pytest.clsA = store.add_class("Cls A")
	
	assert store.get_classes() == [pytest.clsA]

def test_delete_class(store):
	
	pytest.clsB = store.add_class("Cls B")
	store.del_class(pytest.clsA)
	
	assert store.get_classes() == [pytest.clsB]
	
	pytest.clsA = store.add_class("Cls A")

def test_add_member(store):
	
	pytest.clsA.add_member(pytest.obj1)
	pytest.clsA.add_member(pytest.obj2)
	pytest.clsB.add_member(pytest.obj3)
	pytest.clsB.add_member(pytest.obj4)
	
	assert pytest.clsA.get_members() == set([pytest.obj1, pytest.obj2])
	assert pytest.clsB.get_members() == set([pytest.obj3, pytest.obj4])

def test_add_subclass(store):
	
	pytest.clsA = store.add_class("Cls A")
	
	pytest.clsB.add_subclass(pytest.clsA)
	
	assert pytest.clsB.get_subclasses() == [pytest.clsA]
	assert pytest.clsA.get_superclasses() == [pytest.clsB]
	
	assert pytest.clsB.get_members() == set([pytest.obj1, pytest.obj2, pytest.obj3, pytest.obj4])
	pytest.clsB.del_subclass(pytest.clsA)
	
	assert pytest.clsB.get_members() == set([pytest.obj3, pytest.obj4])

def test_add_relation(store):
	
	pytest.obj1.add_relation(pytest.obj3, "A-B")
	pytest.obj1.add_relation(pytest.obj4, "A-B")
	pytest.obj2.add_relation(pytest.obj1, "A-A", weight = 0.123)
	
	assert set(pytest.obj1.get_relations()) == set([(pytest.obj2, "~A-A"), (pytest.obj3, "A-B"), (pytest.obj4, "A-B")])
	assert set(pytest.obj1.get_relations(pytest.obj2)) == set([(pytest.obj2, "~A-A")])
	assert pytest.obj2.get_relation_weight(pytest.obj1, "A-A") == 0.123

def test_add_class_relation(store):
	
	pytest.clsA.add_relation(pytest.clsB, "ClsA-B")
	
	assert set(pytest.clsA.get_relations()) == set([(pytest.clsB, 'ClsA-B')])
	assert set(pytest.clsA.get_object_relations()) == set([(pytest.clsA, 'A-A'), (pytest.clsA, '~A-A'), (pytest.clsB, 'A-B')])

def test_add_descriptor(store):	
	
	pytest.obj1.set_descriptor("Descr A1", 1)
	pytest.obj1.set_descriptor("Descr A2", "X")
	pytest.obj2.set_descriptor("Descr A1", 1.1)
	pytest.obj3.set_descriptor("Descr B", {"value": 2})
	
	assert pytest.obj1.get_descriptor("Descr A1") == 1
	assert pytest.obj1.get_descriptor("Descr A2") == "X"
	assert pytest.obj2.get_descriptor("Descr A1") == 1.1
	assert pytest.obj3.get_descriptor("Descr B") == {"value": 2}
	assert sorted(pytest.obj1.get_descriptor_names()) == ['Descr A1', 'Descr A2']
	assert sorted(pytest.obj2.get_descriptor_names()) == ['Descr A1']
	assert sorted(pytest.obj3.get_descriptor_names()) == ['Descr B']
	assert set(pytest.clsA.get_object_descriptor_names()) == set(['Descr A1', 'Descr A2'])
	assert set(pytest.clsB.get_object_descriptor_names()) == set(['Descr B'])
	assert sorted(store.get_descriptor_names()) == ['Descr A1', 'Descr A2', 'Descr B']

def test_add_class_descriptor(store):
	
	pytest.clsA.set_descriptor("Descr C_A1")
	pytest.clsA.set_descriptor("Descr C_A2")
	pytest.clsB.set_descriptor("Descr C_B")
	
	pytest.clsA.get_descriptor_names()
	
	assert sorted(pytest.clsA.get_descriptor_names()) == ['Descr A1', 'Descr A2', 'Descr C_A1', 'Descr C_A2']
	assert sorted(pytest.clsB.get_descriptor_names()) == ['Descr B', 'Descr C_B']
	assert sorted(store.get_descriptor_names()) == ['Descr A1', 'Descr A2', 'Descr B', 'Descr C_A1', 'Descr C_A2', 'Descr C_B']
	
def test_rename_class(store):
	
	pytest.clsA.rename("Cls A_")
	clsA_ = store.get_class("Cls A_")
	
	assert sorted(store.get_class_names()) == ['Cls A_', 'Cls B', 'Descr A1', 'Descr A2', 'Descr B', 'Descr C_A1', 'Descr C_A2', 'Descr C_B']
	assert clsA_.get_members() == set([pytest.obj1, pytest.obj2])

def test_set_relation_weight(store):
	
	pytest.obj1.add_relation(pytest.obj3, "A-B", weight = 0.456)
	
	assert pytest.obj1.get_relation_weight(pytest.obj3, "A-B") == 0.456

def test_del_member(store):
	
	pytest.clsA.rename("Cls A")
	
	pytest.clsA.del_member(pytest.obj1)
	
	assert pytest.clsA.get_members() == set([pytest.obj2])
	
	pytest.clsA.add_member(pytest.obj2)

def test_del_relation(store):
	
	pytest.obj1.del_relation(pytest.obj3, "A-B")
	
	assert set(pytest.obj1.get_relations()) == set([(pytest.obj2, "~A-A"), (pytest.obj4, "A-B")])
	
	pytest.obj1.add_relation(pytest.obj3, "A-B")

def test_del_class_relation(store):
	
	pytest.clsA.del_relation(pytest.clsB, "ClsA-B")
	
	assert set(pytest.clsA.get_relations()) == set()

def test_del_descriptor(store):
	
	pytest.obj1.del_descriptor("Descr A1")
	
	assert pytest.obj1.get_descriptor("Descr A1") == None
	assert pytest.obj1.get_descriptor("Descr A2") == "X"
	
	pytest.obj1.set_descriptor("Descr A1", 1)

def test_del_class_descriptor(store):
	
	pytest.clsA.del_descriptor("Descr C_A1")
	
	assert sorted(pytest.clsA.get_descriptor_names()) == ['Descr A1', 'Descr A2', 'Descr C_A2']
	
	pytest.clsA.set_descriptor("Descr C_A1")

def test_resource_descriptor(store):
	
	pytest.local_folder = "tests\\test db with spaces"
	if os.path.isdir(pytest.local_folder):
		shutil.rmtree(pytest.local_folder)
	store.set_local_folder(pytest.local_folder)
	sample_folder = "tests\\samples dir with spaces"
	pytest.res_names = []
	for n, filename in enumerate(sorted(os.listdir(sample_folder))):
		path_src = os.path.join(sample_folder, filename)
		name = "Res %d" % (n + 1)
		pytest.obj1.set_resource_descriptor(name, path_src)
		pytest.res_names.append(name)
	pytest.obj1.set_resource_descriptor("Online", "https://picsum.photos/200")
	pytest.res_names.append("Online")
	expected = [
		("200.jpeg", "200.jpeg", True, True),
		("__________.xx.yy.zz", "!@#$%^&() .xx.yy.zz", True, False),
		("image1.jpg", "image1.jpg", True, True),
		("image2.jpg", "image2.jpg", True, True),
		("noext", "noext", True, False),
		("test_pdf_1.pdf", "test_pdf_1.pdf", True, False),
		("test_pdf_2.pdf", "test_pdf_2.pdf", True, False),
		("scsctt.sls", "ščščťť.šľš", True, False),
	]
	for name, exp in zip(sorted(pytest.res_names), expected):
		exp_stored, exp_filename, exp_is_stored, exp_is_image = exp
		res = pytest.obj1.get_descriptor(name)
		url, filename, is_stored, is_image = res.value
		assert os.path.isfile(url_to_path(url)) == True
		assert os.path.split(url)[-1] == exp_stored
		assert exp_filename == filename
		assert exp_is_stored == is_stored
		assert exp_is_image == is_image

def test_geometry_descriptor(store):
	
	coords_point = [1,2]
	
	coords_multipoint_z = [
		[1,2,7],
		[3,4,8],
		[5,6,9],
	]
	
	coords_linestring_m = [
		[1,2,7,10],
		[3,4,8,11],
		[5,6,9,12],
	]
	
	coords_polygon_1 = [
		# exterior
		[
			[1,2],
			[3,4],
			[5,6],
		],
		# holes
		[
			[7,8],
			[9,10],
			[11,12],
		],
		[
			[13,14],
			[15,16],
			[17,18],
		]
	]
	
	coords_polygon_z_1 = [
		# exterior
		[
			[1,2,7],
			[3,4,8],
			[5,6,9],
		],
	]
	
	coords_multipolygon_z_1 = [
		[
			# exterior 1
			[
				(1,2,25),
				(3,4,26),
				(5,6,27),
			],
			# holes 1
			[
				[7,8,28],
				[9,10,29],
				[11,12,30],
			]
		],
		[
			# exterior 2
			[
				[13,14,31],
				[15,16,32],
				[17,18,33],
			],
			# holes 2
			[
				[19,20,34],
				[21,22,35],
				[23,24,36],
			]
		]
	]
	
	coords_multipolygon_m_2 = [
		[
			# exterior 1
			[
				(1,2,25,37),
				(3,4,26,18),
				[5,6,27,39],
			],
		],
		[
			# exterior 2
			[
				[13,14,31,40],
				[15,16,32,41],
				[17,18,33,42],
			],
			# holes 2
			[
				[19,20,34,43],
				[21,22,35,44],
				[23,24,36,45],
			]
		]
	]
	
	pytest.obj4.set_geometry_descriptor("Geo Point", "Point", coords_point, srid = 1234, srid_vertical = 5678)
	pytest.obj4.set_geometry_descriptor("Geo MultiPoint", "MultiPointZ", coords_multipoint_z, srid = 1234)
	pytest.obj4.set_geometry_descriptor("Geo LineString", "LineString", coords_linestring_m)
	pytest.obj4.set_geometry_descriptor("Geo Polygon 1", "POLYGON", coords_polygon_1)
	pytest.obj4.set_geometry_descriptor("Geo PolygonZ 1", "PolygonZ", coords_polygon_z_1)
	pytest.obj4.set_geometry_descriptor("Geo MultiPolygon 1", "MultiPolygonZ", coords_multipolygon_z_1)
	pytest.obj4.set_geometry_descriptor("Geo MultiPolygon 2", "MULTIPOLYGON", coords_multipolygon_m_2)
	
	expected = [
		['SRID=1234;VERT_SRID=5678;POINT(1 2)', 'Point', [1, 2], 1234, 5678],
		['SRID=1234;MULTIPOINTZ(1 2 7, 3 4 8, 5 6 9)', 'MultiPointZ', [[1, 2, 7], [3, 4, 8], [5, 6, 9]], 1234, None],
		['LINESTRINGM(1 2 7 10, 3 4 8 11, 5 6 9 12)', 'LineString', [[1, 2, 7, 10], [3, 4, 8, 11], [5, 6, 9, 12]], None, None],
		['POLYGON((1 2, 3 4, 5 6), (7 8, 9 10, 11 12), (13 14, 15 16, 17 18))', 'POLYGON', [[[1, 2], [3, 4], [5, 6]], [[7, 8], [9, 10], [11, 12]], [[13, 14], [15, 16], [17, 18]]], None, None],
		['POLYGONZ((1 2 7, 3 4 8, 5 6 9))', 'PolygonZ', [[[1, 2, 7], [3, 4, 8], [5, 6, 9]]], None, None],
		['MULTIPOLYGONZ(((1 2 25, 3 4 26, 5 6 27), (7 8 28, 9 10 29, 11 12 30)), ((13 14 31, 15 16 32, 17 18 33), (19 20 34, 21 22 35, 23 24 36)))', 'MultiPolygonZ', [[[[1, 2, 25], [3, 4, 26], [5, 6, 27]], [[7, 8, 28], [9, 10, 29], [11, 12, 30]]], [[[13, 14, 31], [15, 16, 32], [17, 18, 33]], [[19, 20, 34], [21, 22, 35], [23, 24, 36]]]], None, None],
		['MULTIPOLYGONM(((1 2 25 37, 3 4 26 18, 5 6 27 39)), ((13 14 31 40, 15 16 32 41, 17 18 33 42), (19 20 34 43, 21 22 35 44, 23 24 36 45)))', 'MULTIPOLYGON', [[[[1, 2, 25, 37], [3, 4, 26, 18], [5, 6, 27, 39]]], [[[13, 14, 31, 40], [15, 16, 32, 41], [17, 18, 33, 42]], [[19, 20, 34, 43], [21, 22, 35, 44], [23, 24, 36, 45]]]], None, None],
	]
	for name, exp in zip(pytest.obj4.get_descriptor_names(ordered = True), expected):
		geo = pytest.obj4.get_descriptor(name)
		geometry_type, coords, srid, srid_vertical = geo.value
		wkt = geo.wkt
		assert [wkt, geometry_type, coords, srid, srid_vertical] == exp
		
		pytest.obj4.del_descriptor(name)
		store.del_class(name)

def test_datetime_descriptor(store):
	
	date = datetime.datetime.now()
	
	pytest.obj4.set_datetime_descriptor("Date 1", date)
	pytest.obj4.set_datetime_descriptor("Date 2", date.isoformat())
	
	assert pytest.obj4.get_descriptor("Date 1").value == date
	assert pytest.obj4.get_descriptor("Date 2").value == date
	assert pytest.obj4.get_descriptor("Date 1").isoformat == date.isoformat()
	
	pytest.obj4.del_descriptor("Date 1")
	pytest.obj4.del_descriptor("Date 2")
	store.del_class("Date 1")
	store.del_class("Date 2")

def test_descriptor_location(store):
	
	coords_point = [1,2]
	
	coords_polygon = [
		[
			[1,2],
			[3,4],
			[5,6],
		],
	]
	
	pytest.obj1.set_location("Res 2", ("POINT", coords_point))
	pytest.obj1.set_location("Res 3", ("POLYGON", coords_polygon, 123))
	
	assert pytest.obj1.get_location("Res 1") is None
	assert pytest.obj1.get_location("Res 2").value == ('POINT', [1, 2], -1, -1)
	assert pytest.obj1.get_location("Res 3").value == ('POLYGON', [[[1, 2], [3, 4], [5, 6]]], 123, -1)

def test_del_resource(store):
	
	res = pytest.obj1.get_descriptor("Res 1")
	pytest.obj2.set_descriptor("Res A", res)
	for name in pytest.res_names:
		pytest.obj1.del_descriptor(name)
	assert len(store._resources) == 1
	
	pytest.obj2.del_descriptor("Res A")
	assert len(store._resources) == 0
	assert store.get_descriptor_names(ordered = True) == ['Descr A1', 'Descr A2', 'Descr B', 'Descr C_A1', 'Descr C_A2', 'Descr C_B', 'Res A']
	
	for name in pytest.res_names:
		store.del_class(name)
	store.del_class("Res A")
	
	local_folder = store.get_folder()
	assert len(os.listdir(os.path.join(local_folder, "0000"))) == 0
	assert len(os.listdir(os.path.join(local_folder, "_deleted"))) == 8

def test_add_data_row():
	
	store = deposit.Store()
	
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F1",
		},
		relations = set([
			("Area", "contains", "Feature"),
		]),
	)
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F2",
		},
		relations = [
			("Area", "contains", "Feature"),
		],
	)
	cls = store.get_class("Area")
	cls.add_relation("Feature", "contains")
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F3",
		},
	)
	store.add_data_row(
		data = {
			("Area", "Name"): "A1",
			("Feature", "Name"): "A1.F3",
		},
		unique = set(["Feature"])
	)
	store.add_data_row(
		data = {
			("Feature", "Name"): "A1.F4",
		},
	)
	
	query = store.get_query("SELECT Feature.Name, Area.Name")
	
	assert query.columns == [('Feature', 'Name'), ('Area', 'Name')]
	assert [row for row in query] == [[(2, 'A1.F1'), (1, 'A1')], [(3, 'A1.F2'), (1, 'A1')], [(4, 'A1.F3'), (1, 'A1')], [(5, 'A1.F3'), (1, 'A1')], [(6, 'A1.F4'), (None, None)]]

def test_datasource():
	
	def setup_store():

		store = deposit.Store()
		
		# Setting up classes and their members as described in the provided code
		finds = store.add_class("Find")
		features = store.add_class("Feature")
		areas = store.add_class("Area")
		sites = store.add_class("Site")
		
		sites.add_relation(areas, "contains")
		areas.add_relation(features, "contains")
		features.add_relation(finds, "contains")
		
		s1 = sites.add_member()
		s1.set_descriptor("Name", "S1")
		
		a1 = areas.add_member()
		a1.set_descriptor("Name", "A1")
		a2 = areas.add_member()
		a2.set_descriptor("Name", "A2")
		
		fe11 = features.add_member()
		fe11.set_descriptor("Name", "A1.F1")
		fe12 = features.add_member()
		fe12.set_descriptor("Name", "A1.F2")
		fe13 = features.add_member()
		fe13.set_descriptor("Name", "A1.F3")
		fe14 = features.add_member()
		fe14.set_descriptor("Name", "A1.F4")
		fe24 = features.add_member()
		fe24.set_descriptor("Name", "A2.F4")
		fe25 = features.add_member()
		fe25.set_descriptor("Name", "A2.F5")
		
		f111 = finds.add_member()
		f111.set_descriptor("Name", "A1.F1.1")
		f112 = finds.add_member()
		f112.set_descriptor("Name", "A1.F1.2")
		f113 = finds.add_member()
		f113.set_descriptor("Name", "A1.F1.3")
		f121 = finds.add_member()
		f121.set_descriptor("Name", "A1.F2.1")
		f122 = finds.add_member()
		f122.set_descriptor("Name", "A1.F2.2")
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
		
		return store, fe11, fe12, fe24
	
	def clean_up(folder):
		
		if os.path.isdir(folder):
			shutil.rmtree(folder)
	
	def get_store_data(store):
		
		def _get_value(value):
			if isinstance(value, DResource):
				if value.url is None:
					return value_to_str(value)
				return os.path.split(url_to_path(value.url))[-1]
			return value_to_str(value)
		
		classes = []
		cls_relations = []
		objects = []
		obj_relations = []
		members = []
		metadata = [__version__, store._max_order]
		
		for cls in store.get_classes():
			classes.append([
				cls.name,
				cls.order,
				natsorted([descr.name for descr in cls._descriptors]),
			])
			for cls2, label in cls.get_relations():
				cls_relations.append([cls.name, label, cls2.name])
			for obj in cls.get_members():
				members.append([cls.name, obj.id])
			for cls2 in cls.get_subclasses():
				members.append([cls.name, cls2.name])
		for obj in store.get_objects():
			objects.append([
				obj.id,
				natsorted([[descr.name, _get_value(obj.get_descriptor(descr))] for descr in obj.get_descriptors()]),
				natsorted([[descr.name, _get_value(obj.get_location(descr))] for descr in obj.get_descriptors()]),
			])
			for obj2, label in obj.get_relations():
				obj_relations.append([obj.id, label, obj2.id])
		
		data = [metadata, classes, objects, cls_relations, obj_relations, members]
		data = [natsorted(item) for item in data]
		return data
	
	def prepare_folder(folder):
		
		if os.path.isdir(folder):
			shutil.rmtree(folder)
		os.mkdir(folder)
	
	def prepare_db(connstr):
		
		user, password, host, dbname, schema = re.match(r"postgres://(.*?):(.*?)@(.*?)/(.*)\?currentSchema=(.*)", connstr).groups()
		host, port = host.split(":")
		port = int(port)
		conn = psycopg2.connect(
			dbname = dbname,
			user = user,
			password = password,
			host = host,
			port = port,
		)
		cursor = conn.cursor()
		cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = '%s';" % (schema))
		tables = [row[0] for row in cursor.fetchall()]
		for table in tables:
			cursor.execute("DROP TABLE %s.\"%s\";" % (schema, table))
		conn.commit()
		cursor.close()
		conn.close()
	
	src_folder = "tests//test_db_src"
	tgt_folder = "tests//test_db_tgt"
	
	clean_up(src_folder)
	clean_up(tgt_folder)
	
	store_src, fe11, fe12, fe24 = setup_store()
	store_src.set_local_folder(src_folder)
	
	fe11.set_resource_descriptor("Image", "tests//samples dir with spaces//image1.jpg")
	fe12.set_resource_descriptor("Image", "tests//samples dir with spaces//image2.jpg")
	fe12.set_resource_descriptor("File", "tests//samples dir with spaces//ščščťť.šľš")
	fe24.set_resource_descriptor("File", "tests//samples dir with spaces//!@#$%^&() .xx.yy.zz")
	
	coords_point = [1,2]
	coords_polygon = [
		[
			[1,2],
			[3,4],
			[5,6],
		],
	]
	fe11.set_location("Image", ("POINT", coords_point))
	fe12.set_location("Image", ("POLYGON", coords_polygon, 123))
	
	data0 = get_store_data(store_src)
	prepare_folder(tgt_folder)
	store_src.save(path = os.path.join(tgt_folder, "data.json"))
	store = deposit.Store()
	store.load(path = os.path.join(tgt_folder, "data.json"))
	data = get_store_data(store)
	assert data == data0
	
	prepare_folder(tgt_folder)
	store_src.save(path = os.path.join(tgt_folder, "data.pickle"))
	store = deposit.Store()
	store.load(path = os.path.join(tgt_folder, "data.pickle"))
	data = get_store_data(store)
	assert data == data0
	
	connstr_db = "postgres://user:1111@127.0.0.1:5432/deposit_test?currentSchema=public"
	connstr_rel = "postgres://user:1111@127.0.0.1:5432/deposit_test_rel?currentSchema=public"
	prepare_db(connstr_db)
	prepare_db(connstr_rel)
	
	datasource = DB()
	datasource.set_connstr(connstr_db)
	datasource.set_identifier("test1")
	datasource.create()
	datasource.save(store_src)
	prepare_folder(tgt_folder)
	store = deposit.Store()
	store.load(connstr = connstr_db, identifier = "test1")
	data = get_store_data(store)
	assert data == data0
	
	datasource = DBRel()
	datasource.set_connstr(connstr_rel)
	datasource.set_identifier("test1")
	datasource.create()
	datasource.save(store_src)
	prepare_folder(tgt_folder)
	store = deposit.Store()
	store.load(connstr = connstr_rel, identifier = "test1")
	data = get_store_data(store)
	assert data == data0
	
	prepare_db(connstr_db)
	prepare_db(connstr_rel)
	clean_up(src_folder)
	clean_up(tgt_folder)

