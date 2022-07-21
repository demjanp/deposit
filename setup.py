# -*- coding: utf-8 -*-
#!/usr/bin/env python
#

from setuptools import setup, find_packages

from deposit import __version__

setup(
	name='deposit',
	version=__version__,
	author='Peter Demján',
	author_email='peter.demjan@gmail.com',
	packages=find_packages(include = ['deposit', 'deposit.*']),
	install_requires=[
		'networkx>=2.6.3'
	],
	scripts=[],
	license='LICENSE',
	description='Graph-based data storage and exchange',
	long_description=open('README.md').read(),
	python_requires='>=3.10',
)
