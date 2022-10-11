import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	store.load(path = "c:/data_processed/Svodin/svodin.pickle")
	
#	querystr = "SELECT Feature.*"
	querystr = "SELECT Find.*, Feature.*"
#	querystr = "SELECT Feature.*, Find.*"
#	querystr = "SELECT Find.*, Attribute.*"
#	querystr = "SELECT Attribute.*, Find.*"
#	querystr = "SELECT Find.*, Attribute.*, Description.* RELATED Find.descr.Attribute, Description.descr.Find"
	
	query = store.get_query(querystr)
	print()
	print(query.columns)
	print()
	print(len(query))
	print()
#	for row in query:
#		print(row)
#	print()