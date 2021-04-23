from deposit.DModule import (DModule)
from deposit.store.Conversions import (as_url)
from deposit.commander.dialogs.DataSourceMembers._DataSourceFile import (DataSourceFile)

from PySide2 import (QtWidgets, QtCore, QtGui)

from pathlib import Path
import os

class DataSourcePickle(DataSourceFile):
	
	EXTENSION = "pickle"
