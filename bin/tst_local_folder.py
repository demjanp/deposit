import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	store.load(path = "c:/data_processed/test_db4/test4.json")
	store.set_local_folder("c:/data_processed/test_db4_local_folder")
	
	store.save()
	