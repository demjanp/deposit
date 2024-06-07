version_info = (1, 4, 44)

__version__ = '.'.join(map(str, version_info))
__title__ = 'Deposit'
__date__ = "7.6.2024"

from deposit.store.store import Store

from deposit.store.abstract_dtype import AbstractDType
from deposit.store.ddatetime import DDateTime
from deposit.store.dgeometry import DGeometry
from deposit.store.dresource import DResource
