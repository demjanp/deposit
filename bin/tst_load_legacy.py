import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	
#	resp = store.load("Pickle", path = "legacy_db/LAP_example.pickle")
#	resp = store.load("Pickle", path = "legacy_db/arch14cz_filled.pickle")
	resp = store.load("JSON", path = "legacy_db/LAP_example.json")
#	resp = store.load("JSON", path = "legacy_db/arch14cz_filled.json")
	print("loaded legacy:", resp)
	
	print()
	print("store folder:", store.get_folder())
	print()
	
	resp = store.save("Pickle", path = "test_db/lap_example.pickle")
#	resp = store.save("Pickle", path = "test_db/arch14cz_filled.pickle")
#	resp = store.save("JSON", path = "test_db/lap_example.json")
#	resp = store.save("JSON", path = "test_db/arch14cz_filled.json")
	print("saved:", resp)
	
#	resp = store.load("Pickle", path = "test_db/lap_example.pickle")
#	resp = store.load("Pickle", path = "test_db/arch14cz_filled.pickle")
#	resp = store.load("JSON", path = "test_db/lap_example.json")
#	resp = store.load("JSON", path = "test_db/arch14cz_filled.json")
#	print("loaded:", resp)
	
#	resp = store.save("Pickle", path = "test_db/lap_example_2.pickle")
#	resp = store.save("Pickle", path = "test_db/arch14cz_filled.pickle")
#	resp = store.save("JSON", path = "test_db/lap_example_2.json")
#	resp = store.save("JSON", path = "test_db/arch14cz_filled.json")
#	print("saved 2:", resp)
	
