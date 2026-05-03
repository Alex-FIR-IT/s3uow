from typing import Annotated

from pydantic import Field, TypeAdapter

from .types import Media

media_adapter = TypeAdapter(Annotated[Media, Field(discriminator="kind")])
