import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	store.load(path = "c:/data_processed/_exported/data.pickle")
	
	querystr = "SELECT Sample.Id, Feature.Name, Area.Name, Material.Name, Ware.Name"
#	querystr = "SELECT Sample.Id, Material.Name, Ware.Name"
#	querystr = "SELECT Sample.Id, Feature.Name, Area.Name"
	
	query = store.get_query(querystr)
	print()
	print(query.columns)
	print()
#	print(len(query))
#	print()
	for row in query:
		print(row)
	print()