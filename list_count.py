import os

def get_names(path):
	names = []
	for name in os.listdir(path):
		name = os.path.join(path, name)
		if os.path.isdir(name):
			names += get_names(name)
		else:
			names.append(name)
	return names

names = get_names(".")

lines = 0
chars = 0
for name in names:
	if name.endswith(".py"):
		f = open(name, "r")
		contents = f.read()
		if name.endswith("Resources.py"):
			if not contents[:3] == "'''":
				continue
		chars += len(contents)
		lines += len(contents.split("\n"))
		f.close()
print()
print("lines:", lines)
print("chars:", chars)
print()