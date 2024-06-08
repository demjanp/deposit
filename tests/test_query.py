#!/usr/bin/env python

import pytest

import deposit

@pytest.fixture(scope='module')
def store_q():
	
	store = deposit.Store()
	
	finds = store.add_class("Find")
	features = store.add_class("Feature")
	weird = store.add_class(";Weird.Cls, SELECT")
	areas = store.add_class("Area")
	
	a1 = areas.add_member()
	a1.set_descriptor("Name", "A1")
	a2 = areas.add_member()
	a2.set_descriptor("Name", "A2")
	
	fe11 = features.add_member()
	fe11.set_descriptor("Name", "A1.F1")
	fe11.set_descriptor("Area", 2)
	fe12 = features.add_member()
	fe12.set_descriptor("Name", "A1.F2")
	fe12.set_descriptor("Area", 3)
	fe13 = features.add_member()
	fe13.set_descriptor("Name", "A1.F3")
	fe24 = features.add_member()
	fe24.set_descriptor("Name", "A2.F4")
	fe24.set_descriptor("Area", 4)
	fe25 = features.add_member()
	fe25.set_descriptor("Name", "A2.F5")
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	f111.set_descriptor("Material", "Bone")
	f112 = finds.add_member()
	f112.set_descriptor("Name", "A1.F1.2")
	f112.set_descriptor("Material", "Ceramics")
	f113 = finds.add_member()
	f113.set_descriptor("Name", "A1.F1.3")
	f113.set_descriptor("Material", "Ceramics")
	f121 = finds.add_member()
	f121.set_descriptor("Name", "A1.F2.1")
	f121.set_descriptor("Material", "Bronze")
	f122 = finds.add_member()
	f122.set_descriptor("Name", "A1.F2.2")
	f131 = finds.add_member()
	f131.set_descriptor("Name", "A1.F3.1")
	f241 = finds.add_member()
	f241.set_descriptor("Name", "A2.F4.1")
	
	a1.add_relation(fe11, "contains")
	a1.add_relation(fe12, "contains")
	a1.add_relation(fe13, "contains")
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
	fe11.add_relation(fe13, "covers")
	fe24.add_relation(fe25, "disturbs")
	
	w1 = weird.add_member()
	w1.set_descriptor(";Weird.Descr, SELECT", "WA1")
	w2 = weird.add_member()
	w2.set_descriptor(";Weird.Descr, SELECT", "WB1")
	w3 = weird.add_member()
	w3.set_descriptor(";Weird.Descr, SELECT", "WB2")
	
	w2.add_relation(w3, "weird rel, WHERE")
	
	obj = store.add_object()
	obj.set_descriptor("Name", "Classless 1")
	obj = store.add_object()
	obj.set_descriptor("Name", 2)
	
	yield store

def test_select_columns(store_q):
	query = store_q.get_query("SELECT Area, Feature.Name")
	assert query.columns == [('Area', None), ('Feature', 'Name')]
	assert [
		[(1, None), (3, 'A1.F1')],
		[(1, None), (4, 'A1.F2')],
		[(1, None), (5, 'A1.F3')],
		[(2, None), (6, 'A2.F4')],
		[(2, None), (7, 'A2.F5')],
	] == [row for row in query]

def test_select_all_columns(store_q):
	query = store_q.get_query("SELECT Area.*, Feature.*, Find.*")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Area'), ('Feature', 'Name'), ('Find', 'Name'), ('Find', 'Material')]
	assert [
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (8, 'A1.F1.1'), (8, 'Bone')],
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (9, 'A1.F1.2'), (9, 'Ceramics')],
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (10, 'A1.F1.3'), (10, 'Ceramics')],
		[(1, 'A1'), (4, 3), (4, 'A1.F2'), (11, 'A1.F2.1'), (11, 'Bronze')],
		[(1, 'A1'), (4, 3), (4, 'A1.F2'), (12, 'A1.F2.2'), (12, None)],
		[(1, 'A1'), (5, None), (5, 'A1.F3'), (13, 'A1.F3.1'), (13, None)],
		[(2, 'A2'), (6, 4), (6, 'A2.F4'), (14, 'A2.F4.1'), (14, None)],
		[(2, 'A2'), (7, None), (7, 'A2.F5'), (None, None), (None, None)],
	] == [row for row in query]

def test_group_by_columns_with_count(store_q):
	query = store_q.get_query("SELECT Area.Name, Feature.Name, COUNT(Find) AS [Cnt Find] WHERE Find is not None GROUP BY Area.Name, Feature.Name")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Name'), (None, 'Cnt Find')]
	assert [
		[(1, 'A1'), (3, 'A1.F1'), (None, 3)],
		[(1, 'A1'), (4, 'A1.F2'), (None, 2)],
		[(1, 'A1'), (5, 'A1.F3'), (None, 1)],
		[(2, 'A2'), (6, 'A2.F4'), (None, 1)],
	] == [row for row in query]

def test_group_by_with_sum(store_q):
	query = store_q.get_query("SELECT Area.Name, SUM(Feature.Area) AS [SUM Area] GROUP BY Area.Name")
	assert query.columns == [('Area', 'Name'), (None, 'SUM Area')]
	assert [
		[(1, 'A1'), (None, 5.0)],
		[(2, 'A2'), (None, 4.0)],
	] == [row for row in query]

def test_select_where_condition(store_q):
	query = store_q.get_query("SELECT Area.Name, Feature.Name, Find.Name WHERE Find is not None")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Name'), ('Find', 'Name')]
	assert [
		[(1, 'A1'), (3, 'A1.F1'), (8, 'A1.F1.1')],
		[(1, 'A1'), (3, 'A1.F1'), (9, 'A1.F1.2')],
		[(1, 'A1'), (3, 'A1.F1'), (10, 'A1.F1.3')],
		[(1, 'A1'), (4, 'A1.F2'), (11, 'A1.F2.1')],
		[(1, 'A1'), (4, 'A1.F2'), (12, 'A1.F2.2')],
		[(1, 'A1'), (5, 'A1.F3'), (13, 'A1.F3.1')],
		[(2, 'A2'), (6, 'A2.F4'), (14, 'A2.F4.1')],
	] == [row for row in query]

def test_select_with_prefix_condition(store_q):
	query = store_q.get_query("SELECT [;Weird.Cls, SELECT].[;Weird.Descr, SELECT] WHERE [;Weird.Cls, SELECT].[;Weird.Descr, SELECT].startswith('WB')")
	assert query.columns == [(';Weird.Cls, SELECT', ';Weird.Descr, SELECT')]
	assert [
		[(16, 'WB1'),],
		[(17, 'WB2'),],
	] == [row for row in query]

def test_related_items_with_specific_relation(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(Feature, Feature, 'disturbs')")
	assert query.columns == []
	assert [
		[(3, "A1.F1"),],
		[(4, 'A1.F2'),],
		[(6, "A2.F4"),],
		[(7, 'A2.F5'),],
	] == [row for row in query]

def test_related_items_from_specific_object(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(3), Feature, 'disturbs')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(4, 'A1.F2'),],
	] == [row for row in query]

def test_related_items_with_any_relation(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(3), Feature, '*')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(4, 'A1.F2'),],
		[(5, 'A1.F3'),],
	] == [row for row in query]

def test_select_related_items(store_q):
	query = store_q.get_query("SELECT Find.Name, Feature.Name WHERE RELATED(OBJ(3), Find, 'contains')")
	assert query.columns == [('Find', 'Name'), ('Feature', 'Name')]
	assert [
		[(8, 'A1.F1.1'), (3, 'A1.F1')],
		[(9, 'A1.F1.2'), (3, 'A1.F1')],
		[(10, 'A1.F1.3'), (3, 'A1.F1')],
	] == [row for row in query]

def test_select_with_custom_relation(store_q):
	query = store_q.get_query("SELECT [;Weird.Cls, SELECT].* WHERE RELATED([;Weird.Cls, SELECT], [;Weird.Cls, SELECT], 'weird rel, WHERE')")
	assert query.columns == []
	assert [
		[(17, 'WB2'),],
	] == [row for row in query]

def test_select_all_fields(store_q):
	query = store_q.get_query("SELECT Find.*")
	assert query.columns == [('Find', 'Name'), ('Find', 'Material')]
	assert [
		[(8, 'A1.F1.1'), (8, 'Bone')],
		[(9, 'A1.F1.2'), (9, 'Ceramics')],
		[(10, 'A1.F1.3'), (10, 'Ceramics')],
		[(11, 'A1.F2.1'), (11, 'Bronze')],
		[(12, 'A1.F2.2'), (12, None)],
		[(13, 'A1.F3.1'), (13, None)],
		[(14, 'A2.F4.1'), (14, None)],
	] == [row for row in query]

def test_select_all_objects(store_q):
	query = store_q.get_query("SELECT !*")
	assert query.columns == [(None, None)]
	assert [
		[(18, None),],
		[(19, None),],
	] == [row for row in query]

def test_select_all_object_fields(store_q):
	query = store_q.get_query("SELECT !*.*")
	assert query.columns == [(None, 'Name')]
	assert [
		[(18, 'Classless 1'),],
		[(19, 2),],
	] == [row for row in query]

def test_select_filtered_by_condition(store_q):
	query = store_q.get_query("SELECT !*.Name WHERE isinstance(!*.Name, str) and !*.Name.startswith('Class')")
	assert query.columns == [(None, 'Name')]
	assert [
		[(18, 'Classless 1'),],
	] == [row for row in query]
