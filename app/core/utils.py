from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC time as a timezone-naive datetime.

    Replaces the deprecated datetime.utcnow(). Uses timezone-aware
    datetime.now(timezone.utc) internally, then strips tzinfo to stay
    compatible with timezone-naive DateTime DB columns.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
