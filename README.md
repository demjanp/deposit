# <img src="dep_cube.svg" width="32">Deposit
Open source graph database engine focused on scientific data collection.

Created on 29. 4. 2013

<details>
<summary>Table of Contents</summary>

1. [About Deposit](#about)
2. [Installation](#installation)
3. [Contact](#contact)
4. [Acknowledgements](#acknowledgements)
5. [License](#license)

</details>

## About Deposit <a name="about"></a>
Deposit is open source graph database engine that serves as a storage and management platform for both the collection as well as analysis of scientific data. At the data collection stage, it allows maintaining a high granularity of the data, extensive re-use of dictionary entries to facilitate classification, and a high degree of flexibility to modify end extend the database schema as additional information becomes available. For such purposes, the implemented directed graph database format is much more suitable than a relational format.

A typical use case would involve an analytical description of hierarchically classified scientific samples. This format also enables the streamlined merging of collected datasets to a central database or the extraction of subsets for purposes of data analysis or exchange. 

The engine can use a PostgreSQL server as well as the local file system for storage which makes it suitable for field data collection with limited network connectivity. It supports import and export to standard spreadsheet formats (CSV and XLSX) and storage in a relational PostgreSQL format for easy access by external applications.

Deposit also has a [GUI frontend](https://github.com/demjanp/deposit_gui)

It serves as a backend for the following applications:
* [Laser Aided Profiler](https://www.laseraidedprofiler.com/)
* [CeraMatch](https://github.com/demjanp/CeraMatch)


## Installation <a name="installation"></a>

To install the latest version of Deposit from the Python package index, use the following command:
```
pip install deposit
```

For the GUI installer see [Deposit GUI releases](https://github.com/demjanp/deposit_gui/releases/latest)

## Contact: <a name="contact"></a>
Peter Demján (peter.demjan@gmail.com)

Institute of Archaeology of the Czech Academy of Sciences, Prague, v.v.i.

## Acknowledgements <a name="acknowledgements"></a>

Development of this software was supported by OP RDE, MEYS, under the project "Ultra-trace isotope research in social and environmental studies using accelerator mass spectrometry", Reg. No. CZ.02.1.01/0.0/0.0/16_019/0000728.

This software uses the following open source packages:
* [cryptography](https://github.com/pyca/cryptography)
* [natsort](https://github.com/SethMMorton/natsort)
* [NetworKit](https://networkit.github.io/)
* [NetworkX](https://networkx.org/)
* [openpyxl](https://openpyxl.readthedocs.io/)
* [Pillow](https://python-pillow.org/)
* [Psycopg](https://psycopg.org/)
* [PyShp](https://github.com/GeospatialPython/pyshp)
* [PySide2](https://www.pyside.org/)
* [Qt](https://www.qt.io)
* [Shapely](https://github.com/shapely/shapely)
* [Unidecode](https://github.com/avian2/unidecode)
* [validators](https://github.com/kvesteri/validators)

## License <a name="license"></a>

This code is licensed under the [GNU GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details
