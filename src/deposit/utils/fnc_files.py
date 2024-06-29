from deposit.store.dresource import DResource

from urllib.request import pathname2url, url2pathname, urlopen
from urllib.parse import urlparse, urljoin
from unidecode import unidecode
import validators
import tempfile
import filecmp
import certifi
import imghdr
import shutil
import ssl
import sys
import os

IMAGE_EXTENSIONS = ["svg", "png", "jpg", "jpeg", "gif", "tif", "tiff", "bmp"]
MAX_FILES_PER_DIR = 5000

def as_url(value):
	
	value = str(value)
	if is_local_url(value):
		return value
	if validators.url(value):
		return value
	value = os.path.normpath(os.path.abspath(value))
	if value.startswith("\\\\"):
		return "file:" + pathname2url(value)
	return urljoin("file:", pathname2url(value))


def is_local_url(url):
	
	return (urlparse(url).scheme == "file")


def url_to_path(url):
	
	if url is None:
		return None
	parsed = urlparse(url)
	return url2pathname(parsed.path)


def get_temp_path(subdir = "temp", appdir = "deposit"):
	# return temporary path
	
	tempdir = os.path.normpath(os.path.abspath(os.path.join(tempfile.gettempdir(), appdir, subdir)))
	if not os.path.isdir(tempdir):
		try:
			os.makedirs(tempdir)
		except:
			print("Dir not created: %s" % tempdir)
	return tempdir


def clear_temp_dir(appdir = "deposit"):
	
	tempdir = os.path.normpath(os.path.abspath(os.path.join(tempfile.gettempdir(), appdir)))
	if os.path.isdir(tempdir):
		shutil.rmtree(tempdir)


def get_named_path(name, local_folder):
	
	if local_folder is None:
		return get_temp_path(name)
	path = os.path.normpath(os.path.abspath(os.path.join(local_folder, name)))
	if not os.path.isdir(path):
		os.makedirs(path, exist_ok = True)
	return path


def sanitize_filename(filename, default = "file"):
	# return valid filename based on supplied filename, or default if not possible to sanitize
	
	def is_valid_filename(filename):
		# return True if filename is valid
		
		tmp_path = os.path.join(get_temp_path("is_valid_filename"), filename)
		try:
			f = open(tmp_path, "w")
		except:
			return False
		f.close()
		os.remove(tmp_path)
		return True
	
	if not filename:
		return default
	
	filename = unidecode(filename.strip())
	for i in range(len(filename)):
		if not (filename[i].isalnum() or (filename[i] in "._-")):
			filename = filename[:i] + "_" + filename[i+1:]
	if not is_valid_filename(filename):
		return default
	
	return filename


def extract_filename(url, default = "file"):
	# return filename extracted from path
	
	if is_local_url(url):
		url = url_to_path(url)
	
	filename = os.path.basename(url)
	if not filename:
		return default
	
	return filename


def get_unique_path(filename, folder, existing_urls = None):
	
	if existing_urls is None:
		existing_urls = set()
	existing_urls = set([os.path.basename(url) for url in existing_urls])
	
	name, ext = os.path.splitext(filename)
	filenames = set(os.listdir(folder))
	filenames.update(existing_urls)
	newname = name
	n = 1
	while newname + ext in filenames:
		newname = "%s%d" % (name, n)
		n += 1
	return os.path.normpath(os.path.abspath(os.path.join(folder, newname + ext)))


def get_image_format(url, timeout=10):
	# return format (extension) of local image file or None if not recognized
	
	if is_local_url(url):
		path = url_to_path(url)
		ext = os.path.splitext(path)[-1].lower().lstrip(".")
		if ext in IMAGE_EXTENSIONS:
			return ext
		return None
	format = None
	try:
		context = ssl.create_default_context(cafile=certifi.where())
		with urlopen(url, context=context, timeout=timeout) as response:
			format = imghdr.what(None, response.read())
	except Exception as e:
		print(f"GET_IMAGE_FORMAT ERROR: {sys.exc_info()}")
	return format

def update_image_filename(filename, format):
	
	print(f"A:{filename}")  # DEBUG
	if not format:
		return filename
	name, ext = os.path.splitext(filename)
	ext = ext.strip()
	if ext == "":
		ext = "." + format
	print(f"B:{name+ext}")  # DEBUG
	return name + ext	


def get_free_subfolder(local_folder):
	
	found_dirs = {}
	dir_nums = set()
	for dirname in os.listdir(local_folder):
		if not dirname.isdigit():
			continue
		curdir = os.path.join(local_folder, dirname)
		if os.path.isdir(curdir):
			dir_nums.add(int(dirname))
			if (len(os.listdir(curdir)) < MAX_FILES_PER_DIR):
				found_dirs[int(dirname)] = curdir
	if found_dirs:
		return os.path.normpath(os.path.abspath(found_dirs[min(found_dirs.keys())]))
	
	n_max = max(dir_nums) + 1 if dir_nums else 0
	for n in range(n_max + 1):
		if n not in dir_nums:
			break
	folder = os.path.join(local_folder, "%04d" % (n))
	if not os.path.isdir(folder):
		os.makedirs(folder, exist_ok = True)
	return os.path.normpath(os.path.abspath(folder))


def get_updated_local_url(url, local_folder):
	
	if not is_local_url(url):
		return url
	
	local_folder = os.path.normpath(os.path.abspath(local_folder))
	
	path = url_to_path(url)
	if os.path.normpath(os.path.abspath(os.path.split(os.path.dirname(path))[0])) == local_folder:
		if os.path.isfile(path):
			return url
	
	filename = os.path.basename(path)
	for dirname in os.listdir(local_folder):
		if not dirname.isdigit():
			continue
		curdir = os.path.join(local_folder, dirname)
		path2 = os.path.join(curdir, filename)
		if os.path.isfile(path2):
			return as_url(path2)
	
	return None


def prune_local_files(except_paths, local_folder):
	
	del_path = get_named_path("_deleted", local_folder)
	for dirname in os.listdir(local_folder):
		if not dirname.isdigit():
			continue
		curdir = os.path.join(local_folder, dirname)
		for filename in os.listdir(curdir):
			path = os.path.join(curdir, filename)
			if True in [os.path.samefile(path, ex_path) for ex_path in except_paths]:
				continue
			tgt_path = os.path.join(del_path, filename)
			shutil.move(path, tgt_path)
			

def is_same_file(url1, url2):
	
	if not (is_local_url(url1) and is_local_url(url2)):
		return False
	
	return filecmp.cmp(url_to_path(url1), url_to_path(url2))


def store_locally(url, filename, local_folder, existing_urls = None):
	
	filename = sanitize_filename(filename)
	
	try:
		path_dst = get_unique_path(filename, get_free_subfolder(local_folder), existing_urls)
	except:
		print(sys.exc_info())
		return None
	
	if not copy_url(url, path_dst):
		return None
	
	return path_dst


def delete_stored(url, local_folder):
	
	url = get_updated_local_url(url, local_folder)
	if url is None:
		return None, None
	src_path = url_to_path(url)
	if not os.path.isfile(src_path):
		return None, None
	src_filename = os.path.basename(src_path)
	tgt_path0 = os.path.join(get_named_path("_deleted", local_folder), src_filename)
	path, filename = os.path.split(tgt_path0)
	name, ext = os.path.splitext(filename)
	tgt_path = tgt_path0
	n = 1
	while os.path.isfile(tgt_path):
		tgt_path = os.path.join(path, "%s_%d%s" % (name, n, ext))
		n += 1
	shutil.move(src_path, tgt_path)
	return src_filename, tgt_path


def open_url(url, timeout=10):
	
	if is_local_url(url):
		path = url_to_path(url)
		return open(path, "rb")
	try:
		context = ssl.create_default_context(cafile=certifi.where())
		return urlopen(url, context=context, timeout=timeout).read()
	except:
		print("OPEN_URL ERROR:", sys.exc_info())
	return None


def copy_url(url_src, path_dst, timeout=10):
	
	if (not url_src) or (not path_dst):
		return False
	
	if is_local_url(url_src):
		try:
			shutil.copy2(url_to_path(url_src), path_dst)
			return True
		except:
			print("COPY_URL ERROR 1:", sys.exc_info())
		return False
	
	try:
		context = ssl.create_default_context(cafile=certifi.where())
		with urlopen(url_src, context=context, timeout=timeout) as response:
			with open(path_dst, "wb") as f:
				f.write(response.read())
		return True
	except:
		print("COPY_URL ERROR 2:", sys.exc_info())
	
	return False


def copy_resources(resources, src_folder, dst_folder, progress = None):
	# resources = {url: DResource, ...}
	
	cmax = len(resources)
	cnt = 1
	collect = {}
	for url in resources:
		if progress is not None:
			if progress.cancel_pressed():
				return None
			progress.update_state(value = cnt, maximum = cmax)
		cnt += 1
		
		url, filename, is_stored, is_image = resources[url].value
		if is_stored:
			url = get_updated_local_url(url, src_folder)
			url2 = get_updated_local_url(url, dst_folder)
			if is_same_file(url, url2):
				url = url2
			else:
				url = store_locally(url, filename, dst_folder, set(collect.keys()))
		collect[url] = DResource((url, filename, is_stored, is_image))
	
	return collect


