# -*- coding: utf-8 -*-
#!/usr/bin/env python
#

from setuptools import setup, find_packages
import pathlib

import ast
import os

def get_version():
	with open(os.path.join(os.path.dirname(__file__), 'src', 'deposit', '__init__.py')) as f:
		tree = ast.parse(f.read())
		for node in tree.body:
			if isinstance(node, ast.Assign):
				if node.targets[0].id == 'version_info':
					return '.'.join(map(str, ast.literal_eval(node.value)))

try:
	from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
	class bdist_wheel(_bdist_wheel):
		def finalize_options(self):
			_bdist_wheel.finalize_options(self)
			self.root_is_pure = False
except ImportError:
	bdist_wheel = None

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
	name="deposit",
	version=get_version(),
	description="Graph database focused on scientific data collection.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/demjanp/deposit",
	author="Peter Demján",
	author_email="peter.demjan@gmail.com",
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Science/Research",
		"Topic :: Database",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3.10",
		"Operating System :: Microsoft :: Windows :: Windows 10",
	],
	keywords="database, graph",
	package_dir={"": "src"},
	packages=find_packages(where="src"),
	python_requires=">=3.10, <4",
	install_requires=[
		'natsort>=8.2.0, <9',
		'networkit>=10.0, <11',
		'networkx>=2.8.6, <3',
		'openpyxl>=3.0.10, <4',
		'Pillow>=9.2.0, <10',
		'psycopg2>=2.9.3, <3',
		'pyshp>=2.3.1, <3',
		'PySide2>=5.15.2.1, <6',
		'Shapely>=1.8.4, <2',
		'Unidecode>=1.3.4, <2',
		'validators>=0.20.0, <2',
		'cryptography>=38.0.1, <39',
	],
	cmdclass={'bdist_wheel': bdist_wheel},
)
