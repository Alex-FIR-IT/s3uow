from typing import TypeAlias

from fennflow._operations.context.abstract import BaseContext
from fennflow._operations.context.create import CreateContext
from fennflow._operations.context.delete import DeleteContext
from fennflow._operations.context.put import PutContext

Context: TypeAlias = CreateContext | DeleteContext | PutContext | BaseContext
