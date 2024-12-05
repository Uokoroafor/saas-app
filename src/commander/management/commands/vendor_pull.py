from typing import Any
from django.core.management.base import BaseCommand
import helpers
from django.conf import settings
import logging

logger = logging.getLogger("myproject")

STATICFILES_VENDOR_DIR = getattr(settings, "STATICFILES_VENDOR_DIR")

VENDOR_STATICFILES = {
    "saas-theme.min.css": "https://raw.githubusercontent.com/codingforentrepreneurs/SaaS-Foundations/main/src/staticfiles/theme/saas-theme.min.css",
    "flowbite.min.css": "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.css",
    "flowbite.min.js": "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js",
    "flowbite.min.js.map": "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js.map",
}


class Command(BaseCommand):
    """Command to download vendor static files and store them locally.

    This management command iterates through the static files defined
    in `VENDOR_STATICFILES` and downloads each file to the `STATICFILES_VENDOR_DIR`.

    Attributes:
        stdout (OutputWrapper): Standard output used to write messages to the console.
        style (Style): Provides styling methods (e.g., SUCCESS, ERROR) for output.
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """Executes the command to download vendor static files.

        Args:
            *args (Any): Positional arguments passed to the command.
            **options (Any): Keyword options passed to the command.

        Returns:
            None: The function does not return a value.
        """
        self.stdout.write("Downloading vendor static files")
        completed_urls = []

        for name, url in VENDOR_STATICFILES.items():
            out_path = STATICFILES_VENDOR_DIR / name
            dl_success = helpers.download_to_local(url=url, out_path=out_path)
            if dl_success:
                completed_urls.append(url)
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to download {url}")
                )
                logger.error(f"Failed to download {url}")

        if set(completed_urls) == set(VENDOR_STATICFILES.values()):
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully updated all vendor static files."
                )
            )
            logger.info("Successfully updated all vendor static files.")
        else:
            self.stdout.write(
                self.style.WARNING("Failed to download at least one file")
            )

        return
