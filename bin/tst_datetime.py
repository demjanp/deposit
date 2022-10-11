
import deposit

import datetime

if __name__ == "__main__":
	
	store = deposit.Store()
	
	date1 = datetime.datetime.now()
	date2 = date1.isoformat()
	
	obj = store.add_object()
	obj.set_datetime_descriptor("Date 1", date1)
	obj.set_datetime_descriptor("Date 2", date2)
	
	d1 = obj.get_descriptor("Date 1")
	d2 = obj.get_descriptor("Date 2")
	
	print(d1.value == date1)
	print(d2.value == date1)
