'''
	Deposit Server
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	
'''

from deposit import (Store)
from deposit.store.Resources import Resources
from flask import (Flask, request, render_template, send_from_directory, jsonify)
import os

app = Flask(__name__)

class Server(object):
	# main Deposit Server class
	
	def __init__(self, connections):
		# connections = [[DB, File], ...]
		
		global app
		
		app.config["stores"] = {} # {identifier: Store, ...}
		for db, file in connections:
			ident = db.identifier.split("/")[-1].strip("#")
			app.config["stores"][ident] = Store(db, file)
		app.run(host="0.0.0.0", port = 80)

@app.route("/deposit")
@app.route("/deposit/")
def identifiers():
	
	return jsonify(identifiers = dict([(ident, app.config["stores"][ident].identifier()) for ident in app.config["stores"]]))

@app.route("/deposit/<identifier>")
@app.route("/deposit/<identifier>/")
def graph(identifier):
	
	if identifier in app.config["stores"]:
		if ("id" in request.args) and request.args["id"]:
			return "display id: %s#%s" % (identifier, request.args["id"])
		
		else:
			path = app.config["stores"][identifier].get_schema()
			return send_from_directory(*os.path.split(path))
	
	return "Error", 404

@app.route("/deposit/<identifier>/<name>")
def file(identifier, name):
	
	if identifier in app.config["stores"]:
		path = app.config["stores"][identifier].resources.get_path(name)[0]
		if path:
			return send_from_directory(*os.path.split(path))
	
	return "Error", 404

@app.route("/deposit/<identifier>/thumb/<name>")
def thumbnail(identifier, name):
	
	if identifier in app.config["stores"]:
		path = app.config["stores"][identifier].resources.thumbnail(name)[3]
		if path:
			return send_from_directory(*os.path.split(path))
	
	return "Error", 404

@app.route("/deposit/<identifier>/format/<name>")
def format(identifier, name):
	
	if identifier in app.config["stores"]:
		path, _, storage_type = app.config["stores"][identifier].resources.get_path(name)
		online = (storage_type == Resources.RESOURCE_ONLINE)
		connected_online = (storage_type == Resources.RESOURCE_CONNECTED_ONLINE)
		if path:
			format = app.config["stores"][identifier].file.find_image_format(path, online = online, connected_online = connected_online)
			return jsonify(format = format)
	
	return "Error", 404

