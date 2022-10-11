
import deposit
from deposit.utils.fnc_files import (as_url, url_to_path, extract_filename, get_image_format)

from urllib.parse import urlparse, urljoin
from urllib.request import pathname2url, url2pathname, urlopen
import os

if __name__ == "__main__":
	
	store = deposit.Store()
	
#	store.set_local_folder("test_db")
#	store.set_local_folder("c:\\data_processed\\test_db")
	
	sample1 = as_url("c:\\documents_synced\\dc\\_samples\\sample1.jpg")
	sample2 = "https://picsum.photos/200"
	sample3 = "\\\\192.168.1.2\\demjan\\samples\\sample1.jpg"
	sample4 = "p:\\Shared\\sample1.jpg"
	
	url = sample2
	
	resource = store.add_resource(url)
	
	print()
	print(resource.url)
	print(resource.filename)
	print(resource.is_stored)
	print(resource.is_image)
	print()