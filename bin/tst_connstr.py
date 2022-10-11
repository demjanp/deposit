import re

connstr = "postgres://username:password@127.0.0.1:5432/name?currentSchema=schema"
#connstr = "postgres://username:password@server/name"
#connstr = "postgres://username:password@server"

#user, password, host, database = re.match('postgres://(.*?):(.*?)@(.*?)/(.*)', connstr).groups()
user, password, host, database, schema = re.match('postgres://(.*?):(.*?)@(.*?)/(.*)\?currentSchema=(.*)', connstr).groups()

print(user, password, host, database, schema)
