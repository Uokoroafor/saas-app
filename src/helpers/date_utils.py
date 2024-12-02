import datetime


def timestamp_as_datatime(timestamp: float) -> datetime.datetime:
    """
    Converts a Unix timestamp to a timezone-aware datetime object.

    Args:
        timestamp (float): The Unix timestamp to be converted. It represents the
            number of seconds since January 1, 1970 (UTC).

    Returns:
        datetime.datetime: A timezone-aware datetime object corresponding to the
        provided timestamp, with the UTC timezone.

    Raises:
        ValueError: If the timestamp is not a valid Unix timestamp.
    """
    return datetime.datetime.fromtimestamp(
        timestamp=timestamp, tz=datetime.UTC
    )
