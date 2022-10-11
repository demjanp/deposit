import deposit

if __name__ == "__main__":
	
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
		relations = set([
			("Area", "contains", "Feature"),
		]),
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
		unique = set([])
	)
	
	cls = store.get_class("Area")
	print("Area:", [o.id for o in cls.get_members()])
	cls = store.get_class("Feature")
	print("Feature:", [o.id for o in cls.get_members()])
	
#	query = store.get_query("SELECT Area.Name, Feature.Name")
	query = store.get_query("SELECT Feature.Name, Area.Name")
#	query = store.get_query("SELECT Feature.*, Area.*")
#	query = store.get_query("SELECT Area.Name")
#	query = store.get_query("SELECT Feature.Name")
	print()
	print(query.columns)
	print()
	for row in query:
		print(row)
	print()
#	print([row for row in query])

