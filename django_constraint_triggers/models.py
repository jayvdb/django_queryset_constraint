# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q


class M(object):
    def __init__(self, model, error=None, app_label=None, operations=None):
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
            self.operations.append({'type': '__getattribute__', 'name': name})
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


# TODO: Check / reformat name of constraint
class OneNotAllowed(models.Model):
    class Meta:
        constraint_triggers = [
            {
                'name': 'disallow_one',
                'query': M('OneNotAllowed').objects.filter(
                    age=1
                ),
            },
        ]
    age = models.PositiveIntegerField()


import django
if django.VERSION[0] == 2:
    class OneAndTwoNotAllowed(models.Model):
        class Meta:
            constraint_triggers = [
                {
                    'name': 'disallow_one_and_two',
                    'query': M('OneAndTwoNotAllowed').objects.filter(
                        Q(age=1) | Q(age=2)
                    )
                },
            ]
        age = models.PositiveIntegerField()


class OneAndTwoNotAllowedTwoConstraints(models.Model):
    class Meta:
        constraint_triggers = [
            {
                'name': 'disallow_one',
                'query': M('OneAndTwoNotAllowedTwoConstraints').objects.filter(
                    age=1
                )
            },
            {
                'name': 'disallow_two',
                'query': M('OneAndTwoNotAllowedTwoConstraints').objects.filter(
                    age=2
                )
            },
        ]
    age = models.PositiveIntegerField()


from django.db.models.expressions import RawSQL
