import pytest
import deposit

@pytest.fixture(scope='module')
def store_q():
	store = deposit.Store()
	
	# Setting up classes and their members as described in the provided code
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
	fe14 = features.add_member()
	fe14.set_descriptor("Name", "A1.F4")
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
	
	a3 = areas.add_member()
	a3.set_descriptor("Name", "A3")
	
	fe31 = features.add_member()
	fe31.set_descriptor("Name", "A3.F1")
	fe31.set_descriptor("Area", 10)
	
	a3.add_relation(fe31, "contains")
	
	yield store

def test_invalid_query_no_select(store_q):
	
	def fnc_error(message):
		assert message == """QUERY ERROR in "SELCT Feature.Name": no SELECT statement found"""
	
	store_q.set_callback_error(fnc_error)
	query = store_q.get_query("SELCT Feature.Name")	 # Intentional typo in SELECT
	store_q._callback_error.clear()

def test_invalid_query_where_statement(store_q):
	
	def fnc_error(message):
		assert message == """QUERY ERROR in WHERE statement "SELECT Feature.Name WHERE (Feature.Name).startswith(1)": startswith first arg must be str or a tuple of str, not int"""
	
	store_q.set_callback_error(fnc_error)
	query = store_q.get_query("SELECT Feature.Name WHERE (Feature.Name).startswith(1)")	 # Intentional error in WHERE clause
	store_q._callback_error.clear()

def test_empty_results(store_q):
	query = store_q.get_query("SELECT Find.Name WHERE Find.Material == 'Gold'")
	assert query.columns == [('Find', 'Name')]
	assert [] == [row for row in query]

def test_complex_conditions(store_q):
	query = store_q.get_query("SELECT Find.Name, Feature.Area WHERE (Feature.Area is not None) and (int(Feature.Area) <= 2) and (Find.Material == 'Ceramics')")
	assert query.columns == [('Find', 'Name'), ('Feature', 'Area')]
	assert [
		[(10, 'A1.F1.2'), (3, 2)],
		[(11, 'A1.F1.3'), (3, 2)],
	] == [row for row in query]

def test_joins_or_related_queries(store_q):
	query = store_q.get_query("SELECT Find.Name, Feature.Name WHERE RELATED(OBJ(3), Find, 'contains')")
	assert query.columns == [('Find', 'Name'), ('Feature', 'Name')]
	assert [
		[(9, 'A1.F1.1'), (3, 'A1.F1')],
		[(10, 'A1.F1.2'), (3, 'A1.F1')],
		[(11, 'A1.F1.3'), (3, 'A1.F1')],
	] == [row for row in query]

def test_special_characters_in_field_names(store_q):
	query = store_q.get_query("SELECT [;Weird.Cls, SELECT].[;Weird.Descr, SELECT]")
	assert query.columns == [(';Weird.Cls, SELECT', ';Weird.Descr, SELECT')]
	assert [
		[(16, 'WA1')],
		[(17, 'WB1')],
		[(18, 'WB2')],
	] == [row for row in query]

def test_conditions_with_related_chained(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(3), Feature, 'disturbs', chained=True)")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(4, 'A1.F2')],
		[(6, 'A1.F4')],
	] == [row for row in query]

def test_conditions_with_related_circular_1(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(5), Feature, 'covers', chained=True)")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(3, 'A1.F1')],
		[(5, 'A1.F3')],
		[(6, 'A1.F4')],
	] == [row for row in query]

def test_conditions_with_related_circular_2(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(5), Feature, 'covers', chained=False)")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(6, 'A1.F4')],
	] == [row for row in query]

def test_conditions_with_related_circular_3(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(Feature, Feature, 'covers')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(3, 'A1.F1')],
		[(5, 'A1.F3')],
		[(6, 'A1.F4')],
	] == [row for row in query]

def test_group_by_columns_with_count(store_q):
	query = store_q.get_query("SELECT Area.Name, Feature.Name, COUNT(Find) AS [Cnt Find] WHERE Find is not None GROUP BY Area.Name, Feature.Name")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Name'), (None, 'Cnt Find')]
	assert [
		[(1, 'A1'), (3, 'A1.F1'), (None, 3)],
		[(1, 'A1'), (4, 'A1.F2'), (None, 2)],
		[(1, 'A1'), (5, 'A1.F3'), (None, 1)],
		[(2, 'A2'), (7, 'A2.F4'), (None, 1)],
	] == [row for row in query]

def test_group_by_columns_with_count_zero(store_q):
	query = store_q.get_query("SELECT Area.Name, Feature.Name, COUNT(Find) AS [Cnt Find] GROUP BY Area.Name, Feature.Name")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Name'), (None, 'Cnt Find')]
	assert [
		[(1, 'A1'), (3, 'A1.F1'), (None, 3)],
		[(1, 'A1'), (4, 'A1.F2'), (None, 2)],
		[(1, 'A1'), (5, 'A1.F3'), (None, 1)],
		[(1, 'A1'), (6, 'A1.F4'), (None, 0)],
		[(2, 'A2'), (7, 'A2.F4'), (None, 1)],
		[(2, 'A2'), (8, 'A2.F5'), (None, 0)],
		[(21, 'A3'), (22, 'A3.F1'), (None, 0)]
	] == [row for row in query]

def test_group_by_with_sum(store_q):
	query = store_q.get_query("SELECT Area.Name, SUM(Feature.Area) AS [SUM Area] GROUP BY Area.Name")
	assert query.columns == [('Area', 'Name'), (None, 'SUM Area')]
	assert [
		[(1, 'A1'), (None, 5.0)],
		[(2, 'A2'), (None, 4.0)],
		[(21, 'A3'), (None, 10.0)],
	] == [row for row in query]

def test_count_and_sum_aggregation(store_q):
	query = store_q.get_query("SELECT Area.Name, COUNT(Feature) AS [Feature Count] SUM(Feature.Area) AS [Total Area] GROUP BY Area.Name")
	assert query.columns == [('Area', 'Name'), (None, 'Feature Count'), (None, 'Total Area')]
	assert [
		[(1, 'A1'), (None, 4), (None, 5.0)],
		[(2, 'A2'), (None, 2), (None, 4.0)],
		[(21, 'A3'), (None, 1), (None, 10.0)],
	] == [row for row in query]

def test_query_with_object_by_id(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE Feature == 7")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(7, 'A2.F4')],
	] == [row for row in query]

def test_select_columns(store_q):
	query = store_q.get_query("SELECT Area, Feature.Name")
	assert query.columns == [('Area', None), ('Feature', 'Name')]
	assert [
		[(1, None), (3, 'A1.F1')],
		[(1, None), (4, 'A1.F2')],
		[(1, None), (5, 'A1.F3')],
		[(1, None), (6, 'A1.F4')],
		[(2, None), (7, 'A2.F4')],
		[(2, None), (8, 'A2.F5')],
		[(21, None), (22, 'A3.F1')],
	] == [row for row in query]

def test_select_all_columns(store_q):
	query = store_q.get_query("SELECT Area.*, Feature.*, Find.*")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Area'), ('Feature', 'Name'), ('Find', 'Name'), ('Find', 'Material')]
	assert [
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (9, 'A1.F1.1'), (9, 'Bone')],
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (10, 'A1.F1.2'), (10, 'Ceramics')],
		[(1, 'A1'), (3, 2), (3, 'A1.F1'), (11, 'A1.F1.3'), (11, 'Ceramics')],
		[(1, 'A1'), (4, 3), (4, 'A1.F2'), (12, 'A1.F2.1'), (12, 'Bronze')],
		[(1, 'A1'), (4, 3), (4, 'A1.F2'), (13, 'A1.F2.2'), (13, None)],
		[(1, 'A1'), (5, None), (5, 'A1.F3'), (14, 'A1.F3.1'), (14, None)],
		[(1, 'A1'), (6, None), (6, 'A1.F4'), (None, None), (None, None)],
		[(2, 'A2'), (7, 4), (7, 'A2.F4'), (15, 'A2.F4.1'), (15, None)],
		[(2, 'A2'), (8, None), (8, 'A2.F5'), (None, None), (None, None)],
		[(21, 'A3'), (22, 10), (22, 'A3.F1'), (None, None), (None, None)],
	] == [row for row in query]

def test_select_where_condition(store_q):
	query = store_q.get_query("SELECT Area.Name, Feature.Name, Find.Name WHERE Find is not None")
	assert query.columns == [('Area', 'Name'), ('Feature', 'Name'), ('Find', 'Name')]
	assert [
		[(1, 'A1'), (3, 'A1.F1'), (9, 'A1.F1.1')],
		[(1, 'A1'), (3, 'A1.F1'), (10, 'A1.F1.2')],
		[(1, 'A1'), (3, 'A1.F1'), (11, 'A1.F1.3')],
		[(1, 'A1'), (4, 'A1.F2'), (12, 'A1.F2.1')],
		[(1, 'A1'), (4, 'A1.F2'), (13, 'A1.F2.2')],
		[(1, 'A1'), (5, 'A1.F3'), (14, 'A1.F3.1')],
		[(2, 'A2'), (7, 'A2.F4'), (15, 'A2.F4.1')],
	] == [row for row in query]

def test_select_with_bracketed_names(store_q):
	query = store_q.get_query("SELECT [;Weird.Cls, SELECT].[;Weird.Descr, SELECT] WHERE [;Weird.Cls, SELECT].[;Weird.Descr, SELECT].startswith('WB')")
	assert query.columns == [(';Weird.Cls, SELECT', ';Weird.Descr, SELECT')]
	assert [
		[(17, 'WB1')],
		[(18, 'WB2')],
	] == [row for row in query]

def test_related_items_within_class_relation(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(Feature, Feature, 'disturbs')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(3, "A1.F1")],
		[(4, 'A1.F2')],
		[(6, 'A1.F4')],
		[(7, "A2.F4")],
		[(8, 'A2.F5')],
	] == [row for row in query]

def test_related_items_from_specific_object(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(3), Feature, 'disturbs')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(4, 'A1.F2')],
	] == [row for row in query]

def test_related_items_with_any_relation(store_q):
	query = store_q.get_query("SELECT Feature.Name WHERE RELATED(OBJ(3), Feature, '*')")
	assert query.columns == [('Feature', 'Name')]
	assert [
		[(4, 'A1.F2')],
		[(5, 'A1.F3')],
		[(6, 'A1.F4')],
	] == [row for row in query]

def test_select_related_items(store_q):
	query = store_q.get_query("SELECT Find.Name, Feature.Name WHERE RELATED(OBJ(3), Find, 'contains')")
	assert query.columns == [('Find', 'Name'), ('Feature', 'Name')]
	assert [
		[(9, 'A1.F1.1'), (3, 'A1.F1')],
		[(10, 'A1.F1.2'), (3, 'A1.F1')],
		[(11, 'A1.F1.3'), (3, 'A1.F1')],
	] == [row for row in query]

def test_related_items_within_class_relation_bracketed_names(store_q):
	query = store_q.get_query("SELECT [;Weird.Cls, SELECT].* WHERE RELATED([;Weird.Cls, SELECT], [;Weird.Cls, SELECT], 'weird rel, WHERE')")
	assert query.columns == [(';Weird.Cls, SELECT', ';Weird.Descr, SELECT')]
	assert [
		[(17, 'WB1')],
		[(18, 'WB2')],
	] == [row for row in query]

def test_select_all_fields(store_q):
	query = store_q.get_query("SELECT Find.*")
	assert query.columns == [('Find', 'Name'), ('Find', 'Material')]
	assert [
		[(9, 'A1.F1.1'), (9, 'Bone')],
		[(10, 'A1.F1.2'), (10, 'Ceramics')],
		[(11, 'A1.F1.3'), (11, 'Ceramics')],
		[(12, 'A1.F2.1'), (12, 'Bronze')],
		[(13, 'A1.F2.2'), (13, None)],
		[(14, 'A1.F3.1'), (14, None)],
		[(15, 'A2.F4.1'), (15, None)],
	] == [row for row in query]

def test_select_all_objects(store_q):
	query = store_q.get_query("SELECT !*")
	assert query.columns == [(None, None)]
	assert [
		[(19, None)],
		[(20, None)],
	] == [row for row in query]

def test_select_all_object_fields(store_q):
	query = store_q.get_query("SELECT !*.*")
	assert query.columns == [(None, 'Name')]
	assert [
		[(19, 'Classless 1')],
		[(20, 2)],
	] == [row for row in query]

def test_select_filtered_by_condition(store_q):
	query = store_q.get_query("SELECT !*.Name WHERE isinstance(!*.Name, str) and !*.Name.startswith('Class')")
	assert query.columns == [(None, 'Name')]
	assert [
		[(19, 'Classless 1')],
	] == [row for row in query]
