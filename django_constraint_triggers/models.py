# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import models
from django.db.models import (
    Q,
    Value,
    F,
    Count
)
from functools import partial

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
            self.deep_compare(self.operations, other.operations)
        )

    def deep_compare_func(self, left, right):
        # As long as the function and arguments are the same,
        # we don't care if partials are the exact same object.
        if isinstance(left, partial):
            return (
                left.func == right.func and
                left.args == right.args
            )
        else:
            return left == right

    def deep_compare(self, left, right):
        """Recursive compare for dicts / lists with compare_function.
        
        For the compare function, see :code:`deep_compare_func`.
        """
        if type(left) != type(right):
            return False
        elif isinstance(left, dict):
            # Dict comparison
            for key in left:
                if key not in right:
                    return False
                if not self.deep_compare(left[key], right[key]):
                    return False
            return True
        elif isinstance(left, list):
            # List comparison
            if len(left) != len(right):
                return False
            for xleft, xright in zip(left, right):
                if not self.deep_compare(xleft, xright):
                    return False
            return True
        return self.deep_compare_func(left, right)

    def __getitem__(self, key):
        if isinstance(key, slice):
            self.operations.append({'type': '__getitem__', 'key': partial(slice, key.start, key.stop, key.step)})
        else:
            self.operations.append({'type': '__getitem__', 'key': key})
        return self

    def __getattribute__(self, *args, **kwargs):
        try:
            return object.__getattribute__(self, *args, **kwargs)
        except AttributeError:
            self.operations.append({'type': '__getattribute__', 'args': args, 'kwargs': kwargs})
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

class Disallow13Count(AgeModel):
    class Meta:
        constraint_triggers = [{
            # Allow only 1 object in table
            'name': 'Count13',
            'query': M().objects.all()[1:]
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

    class Disallow1Annotate(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Annotate1',
                'query': M().objects.annotate(
                    disallowed=Value(1, output_field=models.IntegerField())
                ).filter(
                    age=F('disallowed')
                )
            }]

    class Disallow1Annotate(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Annotate1',
                'query': M().objects.annotate(
                    disallowed=Value(1, output_field=models.IntegerField())
                ).filter(
                    age=F('disallowed')
                )
            }]

