from datetime import date, datetime
from typing import Any


def to_plain_dict(obj: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy model object into a JSON-safe dict for Redis caching."""
    data = {key: value for key, value in vars(obj).items() if not key.startswith("_")}
    for key, value in list(data.items()):
        if isinstance(value, (datetime, date)):
            data[key] = value.isoformat()
    return data
