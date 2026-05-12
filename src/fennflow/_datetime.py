import datetime

from pydantic import AwareDatetime as PydanticAwareDatetime

AwareDatetime = PydanticAwareDatetime


def now() -> AwareDatetime:
    """Returns a timezone-aware datetime object for current time."""
    return datetime.datetime.now(tz=datetime.timezone.utc)
