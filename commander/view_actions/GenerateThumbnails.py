def get_state(model, view):
	
	return model.has_store(), False

def triggered(model, view, checked):
	
	cmax = model.store._db.relations.shape[0]
	c = 1
	for label, dtype in model.store._db.relations[:,3:]:
		print("\rgenerate thumbnails %d/%d             " % (c, cmax), end = "")
		c += 1
		if (dtype == "DResource") and (label.split(".")[-1].lower() in  model.store.file.images.IMAGE_EXTENSIONS):
			path, _, storage_type = model.store.resources.get_path(label)
			online = (storage_type == model.store.resources.RESOURCE_ONLINE)
			connected_online = (storage_type == model.store.resources.RESOURCE_CONNECTED_ONLINE)
			path = model.store.file.get_thumbnail(path, online = online, connected_online = connected_online)
