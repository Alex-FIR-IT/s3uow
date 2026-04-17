from typing import Annotated
from pydantic import TypeAdapter, Field

from .types import Media

media_adapter = TypeAdapter(Annotated[Media, Field(discriminator='kind')])
