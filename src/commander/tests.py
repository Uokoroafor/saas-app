from django.test import TestCase
from django.conf import settings


# Create your tests here.
class DBTestCase(TestCase):
    def test_db_url_connection_successful(self):
        DATABASE_URL = settings.DATABASE_URL
        self.assertIn("neon.tech", DATABASE_URL)
