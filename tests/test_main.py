"""The main test module."""
from django.test import (
    TestCase,
    override_settings
)
from tests.models import SignalUser

from parameterized import parameterized, parameterized_class


class TestTesting(TestCase):

    def test_tests(self):
        """Test that we can test."""
        self.assertTrue(True)
