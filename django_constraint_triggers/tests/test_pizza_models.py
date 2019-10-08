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

from django_constraint_triggers.models.pizza_models import (
    Pizza,
    PizzaTopping,
    Topping,
    PizzaNC,
    PizzaToppingNC,
    ToppingNC,
)


@parameterized_class([
    {
        "pizza": Pizza,
        "pizza_topping": PizzaTopping,
        "topping": Topping,
        "raises": True,
    },
    {
        "pizza": PizzaNC,
        "pizza_topping": PizzaToppingNC,
        "topping": ToppingNC,
        "raises": False,
    },
])
class TestPizza(TransactionTestCase):

    def assertRaisesIf(self, exception_class, code):
        """Inverse of assertRaisesIf."""
        if self.raises:
            with self.assertRaises(exception_class):
                code(self)
        else:
            code(self)

    def setUp(self):
        # Configure toppings
        self.cheese = self.topping.objects.create(name="Cheese")
        self.ham = self.topping.objects.create(name="Ham")
        self.pepperoni = self.topping.objects.create(name="Pepperoni")
        self.mushrooms = self.topping.objects.create(name="Mushrooms")
        self.onions = self.topping.objects.create(name="Onions")
        self.garlic = self.topping.objects.create(name="Garlic")
        self.pineapple = self.topping.objects.create(name="Pineapple")

    def test_anchovies_are_not_a_valid_topping(self):
        self.assertRaisesIf(
            IntegrityError,
            lambda self: self.topping.objects.create(name="Anchovies")
        )

    def test_max_five_toppings_on_a_pizza(self):
        django_special = self.pizza.objects.create(name="Django Special")
        self.pizza_topping.objects.create(pizza=django_special, topping=self.cheese)
        self.pizza_topping.objects.create(pizza=django_special, topping=self.ham)
        self.pizza_topping.objects.create(pizza=django_special, topping=self.pepperoni)
        self.pizza_topping.objects.create(pizza=django_special, topping=self.mushrooms)
        self.pizza_topping.objects.create(pizza=django_special, topping=self.onions)
        # Adding a 6th topping
        self.assertRaisesIf(
            IntegrityError,
            lambda self: self.pizza_topping.objects.create(pizza=django_special, topping=self.garlic)
        )

    def test_no_pineapple_on_pizza(self):
        django_invalid = self.pizza.objects.create(name="Django Invalid")
        # Adding a 6th topping
        self.assertRaisesIf(
            IntegrityError,
            lambda self: self.pizza_topping.objects.create(pizza=django_invalid, topping=self.pineapple)
        )
