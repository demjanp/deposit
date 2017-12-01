# Deposit

Graph-based data storage and exchange

## Prerequisites

```
python 3.5
PyQt5
PyQt3D
numpy 1.11.0
pyshp 1.2.11 (https://github.com/GeospatialPython/pyshp)
openpyxl 2.4.7 (https://openpyxl.readthedocs.io)
rdflib 4.2.1 (https://github.com/RDFLib/rdflib)
psycopg2
Pillow - Python Imaging Library (Fork) 3.4.1 (http://python-pillow.org)
flask 0.12.2 (http://flask.pocoo.org/)
natsort 5.1.1 (https://pypi.org/project/natsort/)
```

## Deposit (DEP) RDF Schema

### Deposit classes

```
dep:Node - Node of a graph.
dep:Edge - Edge of a graph.
dep:Object - Unlabeled Node. Represents the analytical unit.
dep:Class - Labeled Node. Generalization (synthetical) unit. Only one Class with a specific label can exist.
dep:Member - Unlabeled Edge. Membership of an Object or Class in a Class.
dep:Relation - Labeled Edge. Connection between a Class and an Object or between Objects. Only one Relation between specific Nodes and with a specific label can exist.
dep:Order - rdf:Seq. Ordering of Nodes as specified by their position in a container of this class.
dep:CheckedOut - rdf:Bag. List of Nodes and Edges checked out from a parent Deposit graph.
dep:CheckedOutUpdated - rdf:Bag. List of Nodes and Edges checked out from a parent Deposit graph which have been updated.
dep:CheckedOutDeleted - rdf:Bag. List of Nodes and Edges checked out from a parent Deposit graph which have been deleted.
dep:CheckOutSource - rdfs:Resource. IRI of the source Deposit graph from which the current graph has been checked out.
dep:Changed - rdfs:Literal. Time of last change of a Deposit graph.
dep:Images - rdf:Bag. List of resources which are images.
```

### Deposit properties

```
dep:label - Label of a Node or Edge. Can be numeric, string, resource or geometry.
dep:geotag - Geometric information (wkt) further specifying a resource representing the label of an Edge. Coordinates represent pixels of the raster, [0,0] being the bottom-left corner.
dep:source - Indicates the source Node of an Edge.
dep:target - Indicates the target Node of an Edge.
dep:description - Additional description of a Class, Property or Relation.
dep:projection - Geographic projection as wkt in OGC or ESRI format of a resource representing the label of an Edge.
dep:worldfile_A..F - ESRI world file parameters used for georeferencing raster image resources.

Subclass: A Class which is a Member of another Class.

Descriptor: A Class connected to an Object by a Relation is a Descriptor of the Object and also of its Class. Only one identical Descriptor for a specific Object can exist.

Localy stored files are renamed to [uuid].[ext] and the original names are stored as triplets: uri rdfs:label Literal(name)

Resources are specified by an uri representing a file or online resource; file uri: "http://[Deposit server url]/deposit/file/[graph identifier]/[uuid].[ext]" or e.g. "http://some_server/filename.ext"

Geometry is specified by WKT and optionally EPSG code(s) in GeoSPARQL format stored as wktLiteral.
	e.g.: "<http://www.opengis.net/def/crs/EPSG/0/[srid]> Point(-83.1 34.4)"
	e.g.: "<http://www.opengis.net/def/crs/OGC/1.3/CRS84> Polygon((-83.2 34.3, -83.0 34.3, -83.0 34.5, -83.2 34.3))"
	a vertical coordinate system can also be specified:
		e.g.: "<http://www.opengis.net/def/crs/EPSG/0/[horizontal srid]> <http://www.opengis.net/def/crs/EPSG/0/[vertical srid]> Point(-83.1 34.4)"

Time stamp of last change of the Deposit graph is stored in a Literal
```

### RDFLib definitions

```
The Deposit RDF Schema IRI (Internationalized Resource Identifier):
dep = http://future_url/2017/04/deposit-schema#

A Deposit graph RDF source IRI:
remote graph (served by a Deposit server):
	gra = http://[Deposit server url]/deposit/graph/[graph identifier]#
local graph (stored in a file system):
	gra = file:///[path/to/data]/[graph identifier]#

The GeoSPARQL schema IRI:
ogc = http://www.opengis.net/ont/geosparql#
```

### Deposit graph RDF definitions

```
Object:
	gra:[id_obj] rdf:type dep:Object
	
	id_obj is an Object
	id_obj: obj_1, obj_2, ...

Class:
	gra:[id_cls] rdf:type dep:Class
	gra:[id_cls] dep:label Literal(label)
	
	id_cls is a Class named label
	id_cls: cls_1, cls_2, ...

Member:
	gra:[id_mem] rdf:type dep:Member
	gra:[id_mem] dep:source gra:[id_cls1]
	gra:[id_mem] dep:target gra:[id_obj / id_cls2]
	
	Class id_cls1 has a member Object id_obj or Class id_cls2
	id_mem: mem_1, mem_2, ...

Relation:
	gra:[id_rel] rdf:type dep:Relation
	gra:[id_rel] dep:label Literal(label) / URIRef(label) / wktLiteral(label)
	gra:[id_rel] dep:source gra:[id_obj1 / id_cls1]
	gra:[id_rel] dep:target gra:[id_obj2]
	
	id_rel is a Relation named label
	Object id_obj1 or Class id_cls1 is connected to Object id_obj2 by Relation id_rel
	label can be of type URIRef or wktLiteral only for relations between two Objects
	id_rel: rel_1, rel_2, ...

geotag:
	gra:[id_rel] dep:geotag wktLiteral(wkt)
	
	geometric information wkt further specifies the Relation id_rel

Order:
	gra:order rdf:type dep:Order
	gra:order rdf:_n gra:[id_node]
	
	Node id_node is at the n-th position in Ordering

CheckedOut:
	gra:checked_out rdf:type dep:CheckedOut
	gra:checked_out rdf:_n gra:[id_node]
	
	Node id_node is checked out

CheckedOutUpdated:
	gra:checked_out_updated rdf:type dep:CheckedOutUpdated
	gra:checked_out_updated rdf:_n gra:[id_node]
	
	Node id_node is checked out and was updated

CheckedOutDeleted:
	gra:checked_out_deleted rdf:type dep:CheckedOutDeleted
	gra:checked_out_deleted rdf:_n gra:[id_node]
	
	Node id_node is checked out and was deleted

CheckOutSource:
	URIRef(IRI) rdf:type dep:CheckOutSource
	
	IRI of the source Deposit graph from which the current graph has been checked out.

Changed:
	gra:changed rdf:type dep:Changed
	gra:changed rdf:value Literal(timestamp)
	
	The graph was last changed at time timestamp

Images:
	gra:images rdf:type dep:Images
	gra:images rdf:_n URIRef(label)

description:
	gra:[id] dep:description Literal(d)
	
	d is a description of Class or Relation id

projection:
	gra:[id_rel] dep:projection Literal(wkt)
	
	geographic projection as wkt in OGC or ESRI format (alternative to specifying a SRID) for data associated with the Relation id_rel

worldfile_A..F:
	URIRef(uri) dep:worldfile_A Literal(v)
	URIRef(uri) dep:worldfile_D Literal(v)
	URIRef(uri) dep:worldfile_B Literal(v)
	URIRef(uri) dep:worldfile_E Literal(v)
	URIRef(uri) dep:worldfile_C Literal(v)
	URIRef(uri) dep:worldfile_F Literal(v)
	
	v is a floating point value of ESRI world file parameters A/D/B/E/C/F
	uri is the uri of a local or remote raster image resource
	
	A (line 1): pixel size in the x-direction in map units/pixel.
	D (line 2): rotation about y-axis.
	B (line 3): rotation about x-axis.
	E (line 4): pixel size in the y-direction in map units.
	C (line 5): x-coordinate of the center of the upper left pixel.
	F (line 6): y-coordinate of the center of the upper left pixel.

Locally stored file (served by a Deposit server):
	URIRef([local name].[ext]) rdfs:label Literal([name].[ext])
	
	the original name of localy stored file [local name].[ext] is [name].[ext]
```

## Author

* **Peter Demján** - [peter.demjan@gmail.com](mailto:peter.demjan@gmail.com)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details
