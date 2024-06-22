from deposit.store.abstract_dtype import AbstractDType
from deposit.store.ddatetime import DDateTime
from deposit.store.dgeometry import DGeometry
from deposit.store.dresource import DResource
from deposit.store.ddict import DDict
from deposit.store.dobject import DObject
from deposit.store.dclass import DClass

from deposit.utils.fnc_files import (as_url, get_updated_local_url)
from deposit.utils.fnc_geometry import (add_srid_to_wkt)
from deposit.query.parse import (remove_quoted, remove_bracketed_all)

from cryptography.fernet import Fernet, InvalidToken
from collections import defaultdict
import datetime
import hashlib
import base64
import uuid
import json
import html
import re
import os

GRAPH_ATTRS = dict(
	source = "src", 
	target = "tgt", 
	name = "id",
	key = "lbl", 
	link = "relations"
)

def try_numeric(value):
	
	if isinstance(value, str):
		is_negative = False
		if value.startswith("-"):
			is_negative = True
			value = value[1:]
		if value.isdigit():
			if is_negative:
				return -int(value)
			return int(value)
		if value.replace(".","",1).isdigit():
			if is_negative:
				return -float(value)
			return float(value)
	return value

def dtype_to_dict(value):
	
	if isinstance(value, AbstractDType):
		return value.to_dict()
	if isinstance(value, dict):
		return DDict(value).to_dict()
	return value

def value_to_dtype(value):
	
	if not isinstance(value, dict):
		return value
	value = globals()[value["dtype"]]().from_dict(value)
	if isinstance(value, DDict):
		return value.value
	return value

def value_to_str(value):
	
	if value is None:
		return None
	if isinstance(value, DDateTime):
		return value.isoformat
	if isinstance(value, DGeometry):
		return value.wkt
	if isinstance(value, DResource):
		return value.url
	return str(value)

def parse_connstr(connstr):
	
	values = re.match(r'postgres://(.*?):(.*?)@(.*?)/(.*)\?currentSchema=(.*)', connstr)
	if values is None:
		return {}
	username, password, host, dbname, schema = values.groups()
	return dict(
		username = username,
		password = password,
		host = host,
		dbname = dbname,
		schema = schema,
	)

def legacy_data_to_store(data, store, path, progress = None):
	
	def _as_key(obj_id, is_json):
		
		if is_json:
			return str(obj_id)
		return int(obj_id)
	
	for name in ["classes", "objects"]:
		if name not in data:
			return False
	
	store.clear()
	
	local_folder = None
	if "local_folder" in data:
		local_folder = data["local_folder"]
		store.set_local_folder(local_folder)
	if local_folder is None:	
		local_folder = os.path.normpath(os.path.abspath(os.path.dirname(path)))
	
	is_json = False
	
	obj_id = 0
	for obj_id in data["objects"]:
		obj = DObject(store, int(obj_id) + 1)
		store.G.add_object(int(obj_id) + 1, obj)
	if isinstance(obj_id, str):
		is_json = True
	
	for name in data["classes"]:
		order = data["classes"][name]["order"]
		cls = DClass(store, name, order)
		store.G.add_class(name, cls)
		store._max_order = max(store._max_order, order)
	
	if progress is not None:
		cmax = len(data["objects"]) + len(data["classes"]) + store.G.n_objects() + store.G.n_classes()
		cnt = 1
	
	class_lookup = defaultdict(set)  # {obj_id: set(class_name, ...), ...}
	
	cls_rels_done = set()  # [(src_class, tgt_class, label), ...]
	for name in data["classes"]:
		
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		
		store.G.get_class_data(name).from_dict_1(
			dict(
				descriptors = data["classes"][name]["descriptors"] if "descriptors" in data["classes"][name] else {}
			)
		)
		
		for obj_id in data["classes"][name]["objects"]:
			if _as_key(obj_id, is_json) not in data["objects"]:
				continue
			store.G.add_class_child(name, obj_id + 1)
			class_lookup[obj_id].add(name)
		
		for name_subclass in data["classes"][name]["subclasses"]:
			if name_subclass not in data["classes"]:
				continue
			store.G.add_class_child(name, name_subclass)
		
		if "relations" in data["classes"][name]:
			for label in data["classes"][name]["relations"]:
				for name_tgt in data["classes"][name]["relations"][label]:
					if name_tgt not in data["classes"]:
						continue
					store.G.add_class_relation(name, name_tgt, label)
					cls_rels_done.add((name, name_tgt, label))
	
	collect_rels = set()  # [(src_class, tgt_class, label), ...]
	for obj_id in data["objects"]:
		
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		
		obj_data = dict(
			id = int(obj_id),
			descriptors = {},
			locations = {},
		)
		
		for name in data["objects"][obj_id]["descriptors"]:
			
			dtype = data["objects"][obj_id]["descriptors"][name]["label"]["dtype"]
			value = None
			
			if dtype == "DString":
				value = try_numeric(data["objects"][obj_id]["descriptors"][name]["label"]["value"])
			
			elif dtype == "DDateTime":
				try:
					value = datetime.datetime.fromisoformat(data["objects"][obj_id]["descriptors"][name]["label"]["value"])
				except:
					value = None
				if value is not None:
					value = dict(
						dtype = "DDateTime",
						value = value,
					)
			
			elif dtype == "DGeometry":
				wkt = data["objects"][obj_id]["descriptors"][name]["label"]["value"]
				srid = data["objects"][obj_id]["descriptors"][name]["label"]["srid"]
				srid_vertical = data["objects"][obj_id]["descriptors"][name]["label"]["srid_vertical"]
				wkt = add_srid_to_wkt(wkt, srid, srid_vertical)
				value = dict(
					dtype = "DGeometry",
					value = wkt,
				)
			
			elif dtype == "DResource":
				url = data["objects"][obj_id]["descriptors"][name]["label"]["value"]
				path = data["objects"][obj_id]["descriptors"][name]["label"]["path"]
				filename = data["objects"][obj_id]["descriptors"][name]["label"]["filename"]
				is_image = data["objects"][obj_id]["descriptors"][name]["label"]["image"]
				is_stored = (path is not None)
				if is_stored:
					url = get_updated_local_url(as_url(path), local_folder)
				if url is not None:
					value = dict(
						dtype = "DResource",
						value = (url, filename, is_stored, is_image), 
					)
			
			if value is not None:
				obj_data["descriptors"][name] = value
		
		store.G.get_object_data(int(obj_id) + 1).from_dict_1(obj_data)
		
		for label in data["objects"][obj_id]["relations"]:
			for obj_id_tgt in data["objects"][obj_id]["relations"][label]["objects"]:
				if _as_key(obj_id_tgt, is_json) not in data["objects"]:
					continue
				weight = None
				if ("weights" in data["objects"][obj_id]["relations"][label]) and \
					(_as_key(obj_id_tgt, is_json) in data["objects"][obj_id]["relations"][label]["weights"]):
					weight = data["objects"][obj_id]["relations"][label]["weights"][_as_key(obj_id_tgt, is_json)]
				store.G.add_object_relation(int(obj_id) + 1, int(obj_id_tgt) + 1, label, weight)
				for src_class in class_lookup[int(obj_id)]:
					for tgt_class in class_lookup[int(obj_id_tgt)]:
						collect_rels.add((src_class, tgt_class, label))
	
	collect_rels = cls_rels_done.difference(cls_rels_done)
	for src_class, tgt_class, label in collect_rels:
		store.G.add_class_relation(src_class, tgt_class, label)
	
	for obj in store.G.iter_objects_data():
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		obj.from_dict_2()
	for cls in store.G.iter_classes_data():
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		cls.from_dict_2()
	
	if "user_tools" in data:
		store._user_tools = data["user_tools"]
	
	if "queries" in data:
		store._queries = data["queries"]
	
	store._resources = {}
	for obj in store.get_objects():
		for name in obj.get_descriptor_names():
			descr = obj.get_descriptor(name)
			if isinstance(descr, DResource):
				store._resources[descr.url] = descr
	
	return True

def json_data_to_store(data, store, progress = None):
	
	n_nodes = len(data["object_relation_graph"]["nodes"]) + len(data["class_relation_graph"]["nodes"])
	cmax = 4*n_nodes
	cnt = 1
	if progress is not None:
		progress.update_state(value = cnt, maximum = cmax)
	
	for node in data["object_relation_graph"]["nodes"]:
		if progress is not None:
			if progress.cancel_pressed():
				return True
			progress.update_state(value = cnt, maximum = cmax)
		cnt += 1
		node["data"] = DObject(store, node["id"]).from_dict_1(node["data"])
	for node in data["class_relation_graph"]["nodes"]:
		if progress is not None:
			if progress.cancel_pressed():
				return True
			progress.update_state(value = cnt, maximum = cmax)
		cnt += 1
		node["data"] = DClass(store, node["id"], node["data"]["order"]).from_dict_1(node["data"])
	
	store.clear()
	store.G.objects_from_json(data["object_relation_graph"], GRAPH_ATTRS)
	if progress is not None:
		if progress.cancel_pressed():
			store.clear()
			return True
		progress.update_state(value = cnt, maximum = cmax)
	cnt += n_nodes / 3
	store.G.classes_from_json(data["class_relation_graph"], GRAPH_ATTRS)
	if progress is not None:
		if progress.cancel_pressed():
			store.clear()
			return True
		progress.update_state(value = cnt, maximum = cmax)
	cnt += n_nodes / 3
	store.G.members_from_json(data["class_membership_graph"], GRAPH_ATTRS)
	if progress is not None:
		if progress.cancel_pressed():
			store.clear()
			return True
		progress.update_state(value = cnt, maximum = cmax)
	cnt += n_nodes / 3
	for obj in store.G.iter_objects_data():
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		obj.from_dict_2()
	for cls in store.G.iter_classes_data():
		if progress is not None:
			if progress.cancel_pressed():
				store.clear()
				return True
			progress.update_state(value = cnt, maximum = cmax)
			cnt += 1
		cls.from_dict_2()
	store._max_order = data["max_order"]
	store._user_tools = data["user_tools"]
	store._queries = data["queries"]
	store._local_folder = data["local_folder"]
	store._resources = {}
	for obj in store.get_objects():
		for name in obj.get_descriptor_names():
			descr = obj.get_descriptor(name)
			if isinstance(descr, DResource):
				store._resources[descr.url] = descr
	
	if progress is not None:
		progress.update_state(value = cmax, maximum = cmax)
	
	return True

def select_to_class_descr(select):
	
	select, bracketed = remove_bracketed_all(select)
	select = select.split(".")
	if len(select) != 2:
		return None
	for i in range(2):
		for key in bracketed:
			select[i] = select[i].replace(key, bracketed[key][1:-1])
	return select

def load_user_tool(path):
	
	def _replace_bracketed(substr, bracketed):
		
		for key in bracketed:
			substr = substr.replace(key, bracketed[key][1:-1])
		return substr
	
	markup = ""
	with open(path, "r", encoding = "utf-8") as f:
		markup = f.read()
	
	markup, bracketed = remove_bracketed_all(markup)
	
	elements = []
	# elements = [["Title", title], ["Type", type], tag, group, multigroup, select, unique, ...]
	#	type = "Query" / "SearchForm" / "EntryForm"
	# 	tag = [control type, class.descriptor, label, stylesheet]
	# 	group = [["Group", label], tag, ...], multigroup = [["MultiGroup", label], tag, ...]
	#	select = [class.descriptor]
	collect = []
	idx0 = 0
	while True:
		idx = markup.find("<", idx0)
		value = markup[idx0:idx].strip()
		if value:
			collect[-1].append(value)
		idx0 = idx
		if idx0 == -1:
			break
		idx1 = markup.find(">", idx0)
		if idx1 == -1:
			break
		tag = markup[idx0+1:idx1].strip()
		if tag == "/":
			collect.append(-1)
		else:
			slash_end = tag.endswith("/")
			tag = tag.strip("/").strip()
			if tag:
				tag, quotes = remove_quoted(tag)
				stylesheet = ""
				if " style= _QU" in tag:
					idxs1 = tag.find(" style= _QU")
					idxs2 = tag.find("_ ", idxs1)
					if idxs2 == -1:
						idx0 = idx1 + 1
						continue
					key = tag[idxs1 + 7:idxs2 + 2].strip()
					stylesheet = quotes[key].strip("\"")
					del quotes[key]
					tag = tag[:idxs1]
				tag = [fragment.strip() % quotes for fragment in tag.split(" ")]
				tag = [fragment for fragment in tag if fragment]
				if tag:
					collect.append(tag + [stylesheet])
			if slash_end:
				collect.append(-1)
		idx0 = idx1 + 1
	
	while collect:
		tag = collect.pop(0)
		if not isinstance(tag, list):
			return
		if tag[0] in ["Group", "MultiGroup"]:
			group = [tag]
			while True:
				tag = collect.pop(0)
				if tag == -1:
					break
				group.append(tag.copy())
				if collect.pop(0) != -1:
					return
			elements.append(group)
		else:
			elements.append(tag.copy())
			if collect.pop(0) != -1:
				return
	
	if len(elements) < 3:
		return
	if elements[0][0] != "Title":
		return
	if elements[1][0] != "Type":
		return
	
	data = dict(
		typ = elements[1][1],
		label = elements[0][2],
		elements = []
	)
	if elements[1][1] == "Query":
		if elements[2][0] != "QueryString":
			return
		data["value"] = elements[2][2]
	else:
		for element in elements[2:]:
			if element[0] == "ColumnBreak":
				data["elements"].append(dict(
					typ = "ColumnBreak",
				))
			elif element[0] == "Select":
				dclass, descriptor = element[1].split(".")
				dclass = _replace_bracketed(dclass, bracketed)
				descriptor = _replace_bracketed(descriptor, bracketed)
				data["elements"].append(dict(
					typ = "Select",
					dclass = dclass,
					descriptor = descriptor,
					label = "",
					stylesheet = "",
				))
			elif element[0] == "Unique":
				dclass = element[1]
				data["elements"].append(dict(
					typ = "Unique",
					dclass = dclass,
					label = "",
					stylesheet = "",
				))
			elif isinstance(element[0], list): # Group or MultiGroup
				data["elements"].append(dict(
					typ = element[0][0],
					stylesheet = element[0][1],
					label = element[0][2],
					members = [],
				))
				for typ, select, stylesheet, label in element[1:]:
					dclass, descriptor = select.split(".")
					dclass = _replace_bracketed(dclass, bracketed)
					descriptor = _replace_bracketed(descriptor, bracketed)
					data["elements"][-1]["members"].append(dict(
						typ = typ,
						dclass = dclass,
						descriptor = descriptor,
						label = label,
						stylesheet = stylesheet,
					))
			elif len(element) == 4:  # tag
				typ, select, stylesheet, label = element
				dclass, descriptor = select.split(".")
				dclass = _replace_bracketed(dclass, bracketed)
				descriptor = _replace_bracketed(descriptor, bracketed)
				data["elements"].append(dict(
					typ = typ,
					dclass = dclass,
					descriptor = descriptor,
					label = label,
					stylesheet = stylesheet,
				))
	
	return data

def get_machine_key():
	
	uid = uuid.getnode()
	uid_ = uuid.getnode()
	if uid != uid_:
		key = "rO7%83CsJxD#"
	else:
		key = str(uid)
	key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
	
	return key

def encrypt_password(password):
	
	token = Fernet(get_machine_key()).encrypt(password.encode())
	
	return token.decode()

def decrypt_password(token):
	
	try:
		password = Fernet(get_machine_key()).decrypt(token.encode()).decode()
	except InvalidToken:
		password = ""
	
	return password

def encrypt_connstr(connstr):
	
	parsed = parse_connstr(connstr)
	if not parsed:
		return connstr
	if not parsed["password"]:
		return connstr
	
	token = encrypt_password(parsed["password"])
	connstr = "postgres://%s:-@%s/%s?currentSchema=%s" % (
		parsed["username"],
		parsed["host"], 
		parsed["dbname"], 
		parsed["schema"]
	)
	connstr = html.escape(token) + "\"" + html.escape(connstr)
	
	return connstr

def decrypt_connstr(connstr):
	
	connstr_orig = connstr
	connstr = connstr.split("\"")
	if len(connstr) != 2:
		return connstr_orig
	token, connstr = connstr
	token = html.unescape(token)
	connstr = html.unescape(connstr)
	parsed = parse_connstr(connstr)
	if not parsed:
		return connstr_orig
	password = decrypt_password(token)
	if not password:
		return connstr_orig
	connstr = "postgres://%s:%s@%s/%s?currentSchema=%s" % (
		parsed["username"],
		password,
		parsed["host"], 
		parsed["dbname"], 
		parsed["schema"]
	)
	return connstr

