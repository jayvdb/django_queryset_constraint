"""The main test module."""
from unittest import skipIf, skip

import django
from django.apps import apps
from django.test import (
    TransactionTestCase,
)
from django.db import models
from django.db.utils import IntegrityError
from django.db import transaction

from parameterized import parameterized, parameterized_class
import django_constraint_triggers


def create(self, model, value):
    model.objects.create(age=value)

def update(self, model, value):
    model.objects.create(age=0)
    model.objects.filter(age=0).update(age=value)

def save(self, model, value):
    model(age=value).save()

def bulk_create(self, model, value):
    model.objects.bulk_create([model(age=value)])

def get_or_create(self, model, value):
    model.objects.get_or_create(age=value)

def update_or_create(self, model, value):
    model.objects.update_or_create(age=value)

# Test that our triggers apply to all methods of insertion / updating
@parameterized_class([
    {"save_method": create},
    {"save_method": update},
    {"save_method": save},
    {"save_method": bulk_create},
    {"save_method": get_or_create},
    {"save_method": update_or_create},
])
class TestAge(TransactionTestCase):

    def setUp(self):
        # How many entries to create during each test
        self.num_entries = 4
        self.num_duplicates = 2

    def disallow(self, model_name, disallow, duplicates):
        # Load the test model in
        model = apps.get_model('django_constraint_triggers', model_name)
        # Create all our entries using the parameterized save_method
        for val in range(self.num_entries):
            # Create x duplicates to validate against one-off errors
            for _ in range(self.num_duplicates) if duplicates else [0]:
                # if val is in disallow, we expect it to be rejected by constraint
                if val in disallow:
                    with self.assertRaises(IntegrityError, msg=str(val)):
                        self.save_method(model, val)
                else:
                    self.save_method(model, val)

    @parameterized.expand([
        ['AllowAll', []],
        ['Disallow1QC', [1]],
        ['Disallow1CC', [1]],
        # ['Disallow1ViaQQC', [1]],
        ['Disallow1TriggerNewQC', [1]],
        ['Disallow12InCC', [1,2]],
        ['Disallow12InQC', [1,2]],
        # ['Disallow12ViaQQC', [1,2]],
        ['Disallow12OneFilterCC', [1,2]],
        ['Disallow12OneFilterQC', [1,2]],
        ['Disallow12AndFilterCC', [1,2]],
        ['Disallow12AndFilterQC', [1,2]],
        ['Disallow12MultiFilterCC', [1,2]],
        ['Disallow12MultiFilterQC', [1,2]],
        # ['Disallow12MultiFilterMixed', [1,2]],
        ['Disallow12RangeCC', [1,2]],
        ['Disallow12RangeQC', [1,2]],
        # TODO: Change to range(1, self.num_entries)
        ['AllowOnly0CC', [1,2,3]],
        ['AllowOnly0QC', [1,2,3]],

        # These cannot be done via CheckConstraint
        ['AllowOnly1ObjectQC', [1,2,3], False],  # Fails on duplicate
        ['Disallow1AnnotateQC', [1]],
        ['Disallow1SubqueryQC', [1]],
        ['Disallow13SubquerySliceQC', [1,2,3]],
        ['Disallow13WhenQC', [1,2,3]],
        ['Disallow1SubqueryWith1SubqueryQC', [1]],
        ['Disallow1SubqueryWith2SubqueryQC', [1]],
        ['Disallow1SubqueryWith3SubqueryQC', [1]],
        ['Disallow1SubqueryWith7SubqueryQC', [1]],
    ])
    def test_disallow(self, model, disallow, duplicates=True):
        self.disallow(model, disallow, duplicates)
