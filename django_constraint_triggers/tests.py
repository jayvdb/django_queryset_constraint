"""The main test module."""
from unittest import skipIf

import django
from django.apps import apps
from django.test import (
    TransactionTestCase,
)
from django.db import models
from django.db import InternalError
from django.db import transaction

from parameterized import parameterized, parameterized_class
from django_constraint_triggers.models import *


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

    def disallow(self, model_name, disallow):
        # Load the affected model in
        model = apps.get_model('django_constraint_triggers', model_name)
        # Prepare exception table
        # if 1, expect exception, if 0 do not expect one
        functions = {
            1: [0, 1, 0, 0],
            2: [0, 1, 1, 0],
            3: [0, 1, 1, 1],
        }
        for idx, val in enumerate(functions[disallow]):
            if val:
                with self.assertRaises(InternalError, msg=str(idx)):
                    self.save_method(model, idx)
            else:
                self.save_method(model, idx)

    @parameterized.expand([
        ['Disallow1', 1],
        ['Disallow12In', 2],
        ['Disallow12Range', 2],
        ['Disallow12Multi', 2],
        # ['Disallow13GT', 3],
    ])
    def test_disallow(self, model, disallow):
        self.disallow(model, disallow)

    @parameterized.expand([
        ['Disallow1Q', 1],
        ['Disallow12Q', 2],
        ['Disallow1Annotate', 1],
        ['Disallow13Count', 3],
    ])
    @skipIf(django.VERSION[0] == 1, "Model utilized serialized Q objects")
    def test_disallow_django2(self, model, disallow):
        self.disallow(model, disallow)
