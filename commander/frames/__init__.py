from deposit.commander.frames.Class import (Class)
from deposit.commander.frames.CSV import (CSV)
from deposit.commander.frames.Descriptor import (Descriptor)
from deposit.commander.frames.Query import (Query)
from deposit.commander.frames.Shapefile import (Shapefile)
from deposit.commander.frames.XLSX import (XLSX)

FRAMES = dict([(cls.__name__, cls) for cls in [Class, CSV, Descriptor, Query, Shapefile, XLSX]]) # {name: Frame, ...}
