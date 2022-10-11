import deposit

if __name__ == "__main__":
	
	store = deposit.Store()
	store.load(path = "c:/data_processed/deposit_save_error/data_good.pickle")
#	store.del_object(32) # corrupts data_saved if saved as pickle
#	print("saving json")
#	store.save(path = "c:/data_processed/deposit_save_error/data_saved.json")
#	print("loading json")
#	store.load(path = "c:/data_processed/deposit_save_error/data_saved.json")
#	print("loaded")
	print("saving pickle")
	store.save(path = "c:/data_processed/deposit_save_error/data_saved.pickle")
	print("loading pickle")
	store.load(path = "c:/data_processed/deposit_save_error/data_saved.pickle")
	print("loaded")