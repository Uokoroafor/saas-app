from django.db import models


class PageVisit(models.Model):
    """Model representing a record of a page visit.

    This model stores information about when a user visits a particular page within
    the application. It includes the page path (URL) and the timestamp of the visit.
    Each record corresponds to a single visit.

    Attributes:
        path (str): The URL or path of the page that was visited. This field can be blank or null.
        timestamp (datetime): The timestamp when the page visit occurred. This field is automatically set when the record is created.
    """

    path = models.TextField(
        blank=True, null=True
    )  # The path of the page visited
    timestamp = models.DateTimeField(
        auto_now_add=True
    )  # The timestamp when the visit occurred

    def __str__(self) -> str:
        return f"PageVisit(path={self.path}, timestamp={self.timestamp})"
