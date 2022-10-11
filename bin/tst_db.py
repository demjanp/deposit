import deposit
from deposit.datasource.db import DB

if __name__ == "__main__":
	
	db = DB()
	db.set_username("user")
	db.set_password("1111")
	db.set_host("127.0.0.1")
	db.set_database("deposit_test")
	cursor, tables = db.connect()
	
	print()
	print(cursor)
	print(tables)
	print()
	