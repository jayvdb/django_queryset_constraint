"""The main test module."""
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

from django_constraint_triggers.models.pizza_models import Pizza, PizzaNC


class TestPizza(TransactionTestCase):
    def test_models(self):
        print(Pizza.objects.all())
