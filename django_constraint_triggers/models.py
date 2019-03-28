# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import models
from django.db.models import Q


class M(object):
    def __init__(self, model=None, error=None, app_label=None, operations=None):
        self.model = model
        self.app_label = app_label
        self.operations = operations
        if self.operations is None:
            self.operations = []

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and 
            self.model == other.model and
            self.app_label == other.app_label and
            self.operations == other.operations
        )

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            self.operations.append({'type': '__getattribute__', 'name': str(name)})
            return self

    def __call__(self, *args, **kwargs):
        try:
            return object.__call__(self, *args, **kwargs)
        except TypeError:
            self.operations.append({'type': '__call__', 'args': args, 'kwargs': kwargs})
            return self

    def deconstruct(self):
        return 'django_constraint_triggers.models.' + self.__class__.__name__, [], {
            'model': self.model,
            'app_label': self.app_label,
            'operations': self.operations
        }


# TODO: Move these models into test
# TODO: Check / reformat name of constraint
class AgeModel(models.Model):
    class Meta:
        abstract = True
    age = models.PositiveIntegerField()

class AllowAll(AgeModel):
    pass

# TODO: Changing M to classname results in broken migration
class Disallow1(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': '1',
            'query': M().objects.filter(age=1)
        }]

class Disallow12In(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'IN12',
            'query': M().objects.filter(age__in=[1,2])
        }]

class Disallow12Range(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'GTE1LTE2',
            'query': M().objects.filter(age__gte=1).filter(age__lte=2)
        }]

class Disallow12Multi(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': '1',
            'query': M().objects.filter(age=1)
        }, {
            'name': '2',
            'query': M().objects.filter(age=2)
        }]

class Disallow13GT(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'GTE1',
            'query': M().objects.filter(age__gte=1)
        }]

if django.VERSION[0] >= 2:
    class Disallow1Q(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Q1',
                'query': M().objects.filter(Q(age=1))
            }]

    class Disallow12Q(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Q12',
                'query': M().objects.filter(Q(age=1) | Q(age=2))
            }]
