import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
#	store.load(path = "c:/data_processed/test_db_large/test_db_large.pickle")
	store.load(path = "c:/data_processed/test_db_medium/test_db_medium.pickle")
	
#	query = store.get_query("SELECT Feature.Name, Area.Name")
	query = store.get_query("SELECT Find.Name, Feature.Name, Area.Name")
	print()
	print(query.columns)
	print()
	cnt = 1
	for row in query:
		print(row)
		if cnt == 50:
			break
		cnt += 1
