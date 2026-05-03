from typing import TypeAlias

from fennflow._operations.context.delete import DeleteContext
from fennflow._operations.context.put import PutContext

Context: TypeAlias = PutContext | DeleteContext
