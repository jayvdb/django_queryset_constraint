"""The main test module."""
from unittest import skipIf

import django
from django.test import (
    TransactionTestCase,
)
from django.db import models
from django.db import InternalError
from django.db import transaction

from parameterized import parameterized, parameterized_class
from django_constraint_triggers.models import *


constraint_exception = InternalError


class TestTesting(TransactionTestCase):

    def test_tests(self):
        """Test that we can test."""
        self.assertTrue(True)

    def test_one_not_allowed(self):
        OneNotAllowed.objects.create(age=0)
        with self.assertRaises(constraint_exception):
            OneNotAllowed.objects.create(age=1)
        OneNotAllowed.objects.create(age=2)
        OneNotAllowed.objects.create(age=3)

    @skipIf(django.VERSION[0] == 1, "Model utilized serialized Q objects")
    def test_one_and_two_not_allowed(self):
        OneAndTwoNotAllowed.objects.create(age=0)
        with self.assertRaises(constraint_exception):
            OneAndTwoNotAllowed.objects.create(age=1)
        with self.assertRaises(constraint_exception):
            OneAndTwoNotAllowed.objects.create(age=2)
        OneAndTwoNotAllowed.objects.create(age=3)

    def test_one_and_two_not_allowed_two_constraints(self):
        OneAndTwoNotAllowedTwoConstraints.objects.create(age=0)
        with self.assertRaises(constraint_exception):
            OneAndTwoNotAllowedTwoConstraints.objects.create(age=1)
        with self.assertRaises(constraint_exception):
            OneAndTwoNotAllowedTwoConstraints.objects.create(age=2)
        OneAndTwoNotAllowedTwoConstraints.objects.create(age=3)
