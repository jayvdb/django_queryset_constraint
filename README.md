Django Queryset Constraint
==========================

[![Build Status](https://travis-ci.com/magenta-aps/django_queryset_constraint.svg?branch=master)](https://travis-ci.com/magenta-aps/django_queryset_constraint)
[![Release Status](https://img.shields.io/pypi/v/django_queryset_constraint)](https://pypi.org/project/django-queryset-constraint/)
[![License](https://img.shields.io/pypi/l/django_queryset_constraint)](https://github.com/magenta-aps/django_queryset_constraint/blob/master/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/django_queryset_constraint)](https://www.python.org/downloads/)
[![Django Versions](https://img.shields.io/pypi/djversions/django_queryset_constraint)](https://www.djangoproject.com/download/)



This library enables one to write reliable data invariants, by compiling Django
Querysets to database insert/update triggers, via. the migration system.

Motivation
==========
Django has a built-in signal system, which emits signals on various events, for
instance model creations, updates and deletions. However these signals are not
emmited for queryset operations, and as such cannot be used to maintain data
invariants.

An attempt to ratify this was made with the [Django Queryset Signals](https://github.com/magenta-aps/django-queryset-signals) library.
While this library comes closer to a reliable solution, it does not succeed,
as it is stil possible to break the data invariants by accessing the database
directly.

Database Constraint Triggers will effectively protect against all scenarios.

Installation
============
```
pip install django_queryset_constraint
```

Usage
=====

- Add the `django_queryset_constraint` app to `INSTALLED_APPS`:

```
# settings.py
INSTALLED_APPS = {
    'django_queryset_constraint',
    ...
}
```

*Note: This should be done **before** any apps that will be checked*

- Add `QuerysetConstraint` to `constraints` to the Meta class of the models to checked:

```
# models.py
from django.db import models
from django.db.models import Count
from django_queryset_constraint import M, QuerysetConstraint


class Topping(models.Model):
    name = models.CharField(max_length=30)


class PizzaTopping(models.Model):
    class Meta:
        unique_together = ("pizza", "topping")
        constraints = [
            # A pizza with more than 5 toppings gets soggy
            QuerysetConstraint(
                name='At most 5 toppings',
                queryset=M().objects.values(
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
                queryset=M().objects.filter(
                    topping__name="Pineapple"
                )
            ),
        ]

    pizza = models.ForeignKey('Pizza', on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)

class Pizza(models.Model):
    name = models.CharField(max_length=30)
    toppings = models.ManyToManyField(Topping, through=PizzaTopping)
```

- Make migrations: `python manage.py makemigrations`
- Run migrations: `python manage.py migrate`

*Note: Complex triggers introduce performance overhead.*

Support Matrix
==============
This app supports the following combinations of Django and Python:

| Django | Python   |
| ------ | -------- |
| 2.2    | 3.6, 3.7 |
