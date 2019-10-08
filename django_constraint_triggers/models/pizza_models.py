# -*- coding: utf-8 -*-
from functools import partial

from django.db import models
from django.db.models import (
    Q,
    Value,
    F,
    Count,
    Exists,
    Subquery,
    Case,
    When
)
from django.db.models.expressions import (
    RawSQL,
)

from django_constraint_triggers.utils import M
from django_constraint_triggers.constraints import QuerysetConstraint


DM = partial(M, app_label='django_constraint_triggers')



# No constraint pizzas
class ToppingNC(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class PizzaToppingNC(models.Model):
    pizza = models.ForeignKey('PizzaNC', on_delete=models.CASCADE)
    topping = models.ForeignKey(ToppingNC, on_delete=models.CASCADE)


class PizzaNC(models.Model):
    name = models.CharField(max_length=30)
    toppings = models.ManyToManyField(ToppingNC, through=PizzaToppingNC)

    def __str__(self):
        return self.name


# Limited toppings pizzas
class Topping(models.Model):
    class Meta:
        # While Pineapple can be a valid topping for some things
        # (abeit not pizza), anchovies should never be a topping for anything.
        constraints = [
            models.CheckConstraint(
                name='Anchovies are not a valid topping for anything.',
                check=~Q(name='anchovies'),
            ),
        ]
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class PizzaTopping(models.Model):
    class Meta:
        unique_together = ("pizza", "topping")
        constraints = [
            # A pizza with more than 5 toppings gets soggy
            QuerysetConstraint(
                name='At most 5 toppings',
                queryset=DM('PizzaTopping').objects.values(
                    'pizza'
                ).annotate(
                    num_toppings=Count('topping')
                ).filter(
                    num_toppings__gt=5
                ),
            ),
            # This constraint should be self-explanatory for civilized people
            QuerysetConstraint(
                name='No pineapple',
                queryset=DM('PizzaTopping').objects.filter(
                    topping__name="Pineapple"
                )
            ),
        ]

    pizza = models.ForeignKey('Pizza', on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)


class Pizza(models.Model):
    name = models.CharField(max_length=30)
    toppings = models.ManyToManyField(Topping, through=PizzaTopping)

    def __str__(self):
        return self.name
