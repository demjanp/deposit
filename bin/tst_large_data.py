import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	
#	resp = store.load("Pickle", "legacy_db/KAP_typo.pickle")
#	print("loaded legacy:", resp)
	
	resp = store.load("Pickle", "test_db/KAP_typo.pickle")
	print("loaded:", resp)
	
	print()
	print("store folder:", store.get_folder())
	print()
	
#	resp = store.save("Pickle", "test_db/KAP_typo.pickle")
#	resp = store.save("JSON", "test_db/KAP_typo.json")
#	print("saved:", resp)
