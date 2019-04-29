from deposit import Broadcasts, __version__
from deposit.store.Conversions import (id_to_int, value_to_wkt, wktLiteral_to_wkt, wkt_to_wktLiteral, coords_to_wkt)
from deposit.store.Namespaces import (RDF, RDFS, OGC, DEP)
from deposit.store.DElements.DObjects import (DObject)
from deposit.store.DElements.DClasses import (DClass)
from deposit.store.DLabel.DLabel import (DLabel)
from deposit.store.datasources._DataSource import (DataSource)

from rdflib import (Namespace, Graph, Literal, URIRef)
from urllib.parse import urlparse
import shutil
import datetime
import time
import json
import os

# valid Deposit class names and prefixes used for graph element ids
ID_PREFIX = {
	"Object": "obj",
	"Class": "cls",
	"Member": "mem",
	"Relation": "rel",
}

ESCAPED_CHARS = {
	"\"": "&quot;",
	"'": "&apos;",
	"<": "&lt;",
	">": "&gt;",
	"&": "&amp;",
}

class RDFGraph(DataSource):
	
	def __init__(self, store, url = None):

		DataSource.__init__(self, store)
		
		self.set_url(url)
	
	def set_url(self, url):
		
		if url is None:
			self.url = None
			self.identifier = None
		else:
			self.url = url
			self.identifier = os.path.splitext(url)[0] + "#"
		if self.store.data_source == self:
			self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)
	
	def load(self):

		def to_id(uri):

			return int(uri.split("_")[-1])
		
		def unescape_label(label):
			
			label = str(label)
			for ch in ESCAPED_CHARS:
				label = label.replace(ESCAPED_CHARS[ch], ch)
			return label
		
		if self.identifier is None:
			return False
		if self.url is None:
			return False

		server_url = os.path.split(self.url)[0]
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//")))
		
		GRA = Namespace(self.identifier)
		graph = Graph()
		graph.parse(path, publicID = self.identifier.strip("#"))

		self.store.clear()

		self.stop_broadcasts()
		self.store.events.stop_recording()

		# TODO get local folder from the graph
		self.store.set_local_folder(os.path.split(path)[0])

		class_lookup = {} # {id: DClass(), ...}

		images = [os.path.split(uri)[-1] if uri.startswith(server_url) else str(uri) for _, uri in graph[GRA["images"] : : ] if not uri.endswith("Images")]
		# images = [uri, ...]
		
		stored_paths = self.store.files.get_stored_paths() # {filename: path, ...}
		self.store.images.load_thumbnails()

		resources = {} # {uri: [filename, path], ...}
		for uri, filename in graph[ : RDFS["label"] : ]:
			if isinstance(uri, URIRef) and isinstance(filename, Literal):
				uri = os.path.split(str(uri))[-1]
				filename = filename.value
				if uri in stored_paths:
					resources[uri] = [filename, stored_paths[uri]]

		worldfiles = {} # {uri: [A, D, B, E, C, F], ...}
		for i, letter in enumerate("ADBECF"):
			for s, o in graph[ : DEP["worldfile_%s" % letter] : ]:
				uri = str(s)
				if uri.startswith(server_url):
					uri = os.path.split(uri)[-1]
				if not uri in worldfiles:
					worldfiles[uri] = [.0, .0, .0, .0, .0, .0]
				worldfiles[uri][i] = float(o.value)

		projections = dict([(os.path.split(str(uri))[-1], wkt.value) for uri, wkt in graph[ : DEP["projection"] : ]])
		# projections = {uri: wkt, ...}

		ids = sorted([to_id(s) for s in graph[ : RDF["type"] : DEP["Object"]]])
		for id in ids:
			self.store.objects._members[id] = DObject(self.store.objects, id)
			self.store.objects._keys.append(id)

		classes = [[to_id(s), graph.value(s, DEP["label"], None).value] for s in graph[ : RDF["type"] : DEP["Class"]]]
		if classes:
			order = {} # {id: order, ...}
			for p, o in graph[GRA["order"] : : ]:
				if p != RDF["type"]:
					order[to_id(o)] = int(p.split("_")[-1])
			classes = sorted(classes, key = lambda row: order[row[0]])
			for id, name in classes:
				name = unescape_label(json.loads(name))
				self.store.classes._members[name] = DClass(self.store.classes, name, order[id])
				self.store.classes._keys.append(name)
				class_lookup[id] = self.store.classes._members[name]
		
		members = {} # {id: [source, target], ...}
		relations = {} # {id: [source, target, label, dtype], ...}

		for s, o in graph[ : DEP["source"] : ]:
			id, id_src = str(s).split("#")[-1], str(o).split("#")[-1]
			if id.startswith(ID_PREFIX["Member"]):
				members[id] = [id_src]
			else:
				relations[id] = [id_src]

		for s, o in graph[ : DEP["target"] : ]:
			id, id_tgt = str(s).split("#")[-1], str(o).split("#")[-1]
			if id.startswith(ID_PREFIX["Member"]):
				members[id].append(id_tgt)
			else:
				relations[id].append(id_tgt)

		if relations:
			for s, label in graph[ : DEP["label"] : ]:
				id = str(s).split("#")[-1]
				if id.startswith(ID_PREFIX["Relation"]):
					if isinstance(label, Literal) and (label.datatype == OGC.wktLiteral):
						dtype = "DGeometry"
						label = unescape_label(label)
					elif isinstance(label, URIRef):
						dtype = "DResource"
						label = unescape_label(label)
						if label.startswith(server_url):
							label = os.path.split(label)[-1]
					else:
						dtype = "DString"
						label = unescape_label(json.loads(label.value))
					relations[id] += [label, dtype]
		
		for id in members:
			id_src, id_tgt = members[id]
			if id_tgt.startswith(ID_PREFIX["Object"]):
				self.store.objects[to_id(id_tgt)].classes.add(class_lookup[to_id(id_src)])
			else:
				class_lookup[to_id(id_src)].subclasses.add(class_lookup[to_id(id_tgt)])
		
		geotags = {} # {rel_id: label, ...}
		for s, o in graph[ : DEP["geotag"] : ]:
			geotags[str(s).split("#")[-1]] = wkt_to_wktLiteral(*value_to_wkt(str(o), -1, -1))
		
		for id in relations:
			id_src, id_tgt, label, dtype = relations[id]
			if id_src.startswith(ID_PREFIX["Class"]):
				descriptor = self.store.objects[to_id(id_tgt)].descriptors.add(class_lookup[to_id(id_src)], DLabel(label).asdtype(dtype))
				if descriptor.label.__class__.__name__ == "DResource":
					value = descriptor.label.value
					if value in projections:
						descriptor.label.set_projection(projections[value])
					if value in worldfiles:
						descriptor.label.set_worldfile(worldfiles[value])
					if value in resources:
						descriptor.label.set_stored(*resources[value])
					if value in images:
						descriptor.label.set_image(True)
				if id in geotags:
					descriptor.geotag = geotags[id]
			else:
				self.store.objects[to_id(id_src)].relations.add(label, self.store.objects[to_id(id_tgt)])

		changed = graph.value(GRA["changed"], RDF.value, None)
		if not changed is None:
			self.store.changed = changed.value
		
		self.store.set_datasource(self)
		
		self.store.events.resume_recording()
		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)

		return True

	def save(self):
		
		def escape_label(label):
			
			for ch in ESCAPED_CHARS:
				label = label.replace(ch, ESCAPED_CHARS[ch])
			return label
		
		def get_id(id, typ):
			
			return "%s_%d" % (ID_PREFIX[typ], id)
		
		if self.url is None:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
			return False
		
		parsed = urlparse(self.url)
		path = os.path.normpath(os.path.abspath(parsed.path.strip("//")))
		
		if os.path.isfile(path):
			back_path = self.store.files.get_backup_path()
			tgt_file, ext = os.path.splitext(os.path.split(path)[1])
			tgt_file = "%s_%s" % (tgt_file, datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d'))
			n = 1
			while True:
				tgt_path = os.path.join(back_path, "%s_%d%s" % (tgt_file, n, ext))
				if not os.path.isfile(tgt_path):
					break
				n += 1
			shutil.move(path, os.path.join(back_path, tgt_path))
		
		with open(path, "w", encoding = "utf-8") as f:
			
			# header
			f.write('''<?xml version="1.0" encoding="UTF-8"?>\n''')
			f.write('''<!--\n''')
			f.write('''\tRDF Schema of a Deposit database\n''')
			f.write('''\tCreated: %s\n''' % (datetime.date.today().isoformat()))
			f.write('''-->\n''')
			f.write('''<rdf:RDF\n''')
			f.write('''\txmlns:rdf="%s"\n''' % RDF)
			f.write('''\txmlns:rdfs="%s"\n''' % RDFS)
			f.write('''\txmlns:ogc="%s"\n''' % OGC)
			f.write('''\txmlns:dep="%s"\n''' % DEP)
			f.write('''>\n''')
			
			# objects
			for id in self.store.objects:
				f.write('''\t<dep:Object rdf:about="#%s"/>\n''' % (get_id(id, "Object")))
			
			# classes
			id_cls = 0
			for name in self.store.classes:
				cls = self.store.classes[name]
				f.write('''\t<dep:Class rdf:about="#%s">\n''' % (get_id(id_cls, "Class")))
				f.write('''\t\t<dep:label>%s</dep:label>\n''' % (json.dumps(escape_label(name))))
				f.write('''\t</dep:Class>\n''')
				id_cls += 1
			
			# order of classes
			order = [] # [[order, class id], ...]
			for name in self.store.classes:
				cls = self.store.classes[name]
				order.append([cls.order, cls.id])
			order = sorted(order, key = lambda row: row[0])
			f.write('''\t<dep:Order rdf:about="#order">\n''')
			for ord, id in order:
				f.write('''\t\t<rdf:_%d rdf:resource = "#%s"/>\n''' % (ord, get_id(id, "Class")))
			f.write('''\t</dep:Order>\n''')
			
			# members
			id_mem = 0
			for name in self.store.classes:
				cls = self.store.classes[name]
				id_src = cls.id
				for id_tgt in cls.objects:
					f.write('''\t<dep:Member rdf:about="#%s">\n''' % (get_id(id_mem, "Member")))
					f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (get_id(id_src, "Class")))
					f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (get_id(id_tgt, "Object")))
					f.write('''\t</dep:Member>\n''')
					id_mem += 1
				for id_tgt in cls.subclasses:
					f.write('''\t<dep:Member rdf:about="#%s">\n''' % (get_id(id_mem, "Member")))
					f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (get_id(id_src, "Class")))
					f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (get_id(id_tgt, "Class")))
					f.write('''\t</dep:Member>\n''')
					id_mem += 1
			
			id_rel = 0
			
			# relations
			for id_src in self.store.objects:
				for rel in self.store.objects[id_src].relations:
					if not rel.startswith("~"):
						for id_tgt in self.store.objects[id_src].relations[rel]:
							f.write('''\t<dep:Relation rdf:about="#%s">\n''' % (get_id(id_rel, "Relation")))
							f.write('''\t\t<dep:label>%s</dep:label>\n''' % (json.dumps(escape_label(rel))))
							f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (get_id(id_src, "Object")))
							f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (get_id(id_tgt, "Object")))
							f.write('''\t</dep:Relation>\n''')
							id_rel += 1
			
			# descriptors
			worldfiles = [] # [[uri, A, D, B, E, C, F], ...]
			projections = [] # [[uri, wkt], ...]
			resources = [] # [[uri, filename], ...]
			images = [] # [uri, ...]
			for id_tgt in self.store.objects:
				for name in self.store.objects[id_tgt].descriptors:
					descr = self.store.objects[id_tgt].descriptors[name]
					id_src = descr.dclass.id
					dtype = descr.label.__class__.__name__
					label = escape_label(descr.label.value)
					f.write('''\t<dep:Relation rdf:about="#%s">\n''' % (get_id(id_rel, "Relation")))
					if dtype == "DGeometry":
						f.write('''\t\t<dep:label rdf:datatype="%swktLiteral">%s</dep:label>\n''' % (OGC, label))
					elif dtype == "DResource":
						f.write('''\t\t<dep:label rdf:resource="%s"/>\n''' % (label))
						if not descr.label.worldfile is None:
							worldfiles.append([label] + descr.label.worldfile)
						if not descr.label.projection is None:
							projections.append([label, descr.label.projection])
						if descr.label.is_stored():
							resources.append([label, descr.label.filename])
						if descr.label.is_image():
							images.append(label)
					else:
						f.write('''\t\t<dep:label>%s</dep:label>\n''' % (json.dumps(label)))
					if not descr.geotag is None:
						f.write('''\t\t<dep:geotag rdf:datatype="%swktLiteral">%s</dep:geotag>\n''' % (OGC, escape_label(descr.geotag)))
					f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (get_id(id_src, "Class")))
					f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (get_id(id_tgt, "Object")))
					f.write('''\t</dep:Relation>\n''')
					id_rel += 1
			
			# worldfiles
			for row in worldfiles:
				f.write('''\t<rdfs:Resource rdf:about="%s">\n''' % (row[0]))
				for i, letter in enumerate("ADBECF"):
					f.write('''\t\t<dep:worldfile_%s rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">%s</dep:worldfile_%s>\n''' % (letter, row[i + 1], letter))
				f.write('''\t</rdfs:Resource>\n''')
			
			# projections
			for uri, wkt in projections:
				f.write('''\t<rdfs:Resource rdf:about="%s">\n''' % (uri))
				f.write('''\t\t<dep:projection rdf:datatype="http://www.w3.org/2001/XMLSchema#string">%s</dep:projection>\n''' % (wkt))
				f.write('''\t</rdfs:Resource>\n''')
			
			# resources
			for uri, filename in resources:
				f.write('''\t<rdfs:Resource rdf:about="%s">\n''' % (uri))
				f.write('''\t\t<rdfs:label>%s</rdfs:label>\n''' % (filename))
				f.write('''\t</rdfs:Resource>\n''')
			
			# images
			f.write('''\t<dep:Images rdf:about="#images">\n''')
			for i, uri in enumerate(images):
				f.write('''\t\t<rdf:_%d rdf:resource = "%s"/>\n''' % (i + 1, uri))
			f.write('''\t</dep:Images>\n''')
			
			# changed
			f.write('''\t<dep:Changed rdf:about="#changed">\n''')
			f.write('''\t\t<rdf:value rdf:datatype="http://www.w3.org/2001/XMLSchema#double">%s</rdf:value>\n''' % (self.store.changed))
			f.write('''\t</dep:Changed>\n''')
			
			f.write('''</rdf:RDF>\n''')
		
		self.broadcast(Broadcasts.STORE_SAVED)
		return True