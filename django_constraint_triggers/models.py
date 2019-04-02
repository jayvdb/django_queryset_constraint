# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import apps

import django
from django.db import models
from django.db.models import (
    Q,
    Value,
    F,
    Count,
    Exists,
    OuterRef,
    Subquery
)
from django.db.models.expressions import (
    RawSQL,
)
from functools import partial


class M(object):
    """A :code:`M()` object is a lazy object utilized in place of Queryset(s).

    It is utilized when a Queryset cannot be used directly, for instance when a
    Queryset needs to be symbolically serialized to the disk, as is the case
    when generating migration files.

    It is a simple object, which simply records model name and app_label, such
    that the model can be retrieved, along with a stack of operations applied
    to the M object, such that these operations can be replayed to reconstruct
    the Queryset at a later time.
    """

    def __init__(self, model, app_label, operations=None, finalized=False):
        """Construct an M object.

        Args:
            model (str, optional):
                Name of the model to apply the recorded M operations to.
                If :code:`None`, it defaults to the model upon which the M 
                object is constructed.
            app_label (str, optional):
                Application label for the model (previous argument).
                If :code:`None`, it defaults to the label where the M object
                is constructed.
            operations (list of dict, optional):
                Should not be supplied by the user.
        """
        self.model = model
        self.app_label = app_label
        self.operations = operations
        self.finalized = finalized
        if self.operations is None:
            self.operations = []

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and 
            self.model == other.model and
            self.app_label == other.app_label and
            self.__deep_compare(self.operations, other.operations)
        )

    @staticmethod
    def deep_deconstruct(node):
        if isinstance(node, dict):
            # Dict comparison
            for key in node:
                node[key] = M.deep_deconstruct(node[key])
        elif isinstance(node, list) or isinstance(node, tuple):
            node = list(node)
            for idx in range(len(node)):
                node[idx] = M.deep_deconstruct(node[idx])
        elif hasattr(node, 'deconstruct'):
            node = node.deconstruct()
            node = M.deep_deconstruct(node)
        return node

    def replay(self):
        # Run through all operations to generate our queryset
        # TODO: Apply rules recursively to subqueries
        # TODO: Support Q and F in Django 1.11 using partials
        model = apps.get_model(self.app_label, self.model)
        result = model
        for operation in self.operations:
            if operation['type'] == '__getitem__':
                arg = operation['key']
                if isinstance(arg, partial):
                    arg = arg()
                result = result.__getitem__(arg)
            elif operation['type'] == '__getattribute__':
                result = getattr(result, *operation['args'], **operation['kwargs'])
            elif operation['type'] == '__call__':
                result = result(*operation['args'], **operation['kwargs'])
            else:
                raise Exception("Unknown operation!")
        return result

    def __deep_compare_func(self, left, right):
        # As long as the function and arguments are the same,
        # we don't care if partials are the exact same object.
        if isinstance(left, partial):
            return (
                left.func == right.func and
                left.args == right.args
            )
        else:
            return left == right

    def __deep_compare(self, left, right):
        """Recursive compare for dicts / lists with compare_function.
        
        For the compare function, see :code:`__deep_compare_func`.
        """
        if type(left) != type(right):
            return False
        elif isinstance(left, dict):
            # Dict comparison
            for key in left:
                if key not in right:
                    return False
                if not self.__deep_compare(left[key], right[key]):
                    return False
            return True
        elif isinstance(left, list):
            # List comparison
            if len(left) != len(right):
                return False
            for xleft, xright in zip(left, right):
                if not self.__deep_compare(xleft, xright):
                    return False
            return True
        return self.__deep_compare_func(left, right)

    def __getitem__(self, key):
        if self.finalized:
            return self.replay().__getitem__(key)

        if isinstance(key, slice):
            self.operations.append({'type': '__getitem__', 'key': partial(slice, key.start, key.stop, key.step)})
        else:
            self.operations.append({'type': '__getitem__', 'key': key})
        return self

    def __getattribute__(self, *args, **kwargs):
        try:
            return object.__getattribute__(self, *args, **kwargs)
        except AttributeError as exc:
            if self.finalized:
                return self.replay().__getattribute__(*args, **kwargs)
            self.operations.append({'type': '__getattribute__', 'args': args, 'kwargs': kwargs})
            return self

    def __call__(self, *args, **kwargs):
        try:
            return object.__call__(self, *args, **kwargs)
        except TypeError as exc:
            if self.finalized:
                return self.replay().__call__(*args, **kwargs)
            self.operations.append({'type': '__call__', 'args': args, 'kwargs': kwargs})
            return self

    def deconstruct(self):
        return 'django_constraint_triggers.models.' + self.__class__.__name__, [], {
            'model': self.model,
            'app_label': self.app_label,
            'operations': self.operations,
            'finalized': True,
        }

DM = partial(M, app_label='django_constraint_triggers')


# TODO: Move these models into test
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
            'query': DM('Disallow1').objects.filter(age=1)
        }]

class Disallow12In(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'IN12',
            'query': DM('Disallow12In').objects.filter(age__in=[1,2])
        }]

class Disallow12Double(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'GTE1LTE2',
            'query': DM('Disallow12Double').objects.filter(age__gte=1).filter(age__lte=2)
        }]

class Disallow12Multi(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': '1',
            'query': DM('Disallow12Multi').objects.filter(age=1)
        }, {
            'name': '2',
            'query': DM('Disallow12Multi').objects.filter(age=2)
        }]

class Disallow13GT(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'GTE1',
            'query': DM('Disallow13GT').objects.filter(age__gte=1)
        }]

class Disallow13Count(AgeModel):
    class Meta:
        constraint_triggers = [{
            # Allow only 1 object in table (by using offset 1)
            'name': 'Count13',
            'query': DM('Disallow13Count').objects.all()[1:]
        }]

class AllowOnly0(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Only1',
            'query': DM('AllowOnly0').objects.exclude(age=0)
        }]

class Disallow12Range(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Range12',
            'query': DM('Disallow12Range').objects.filter(age__range=(1,2))
        }]

# These need django 2+ for serialization of queryset expressions.
if django.VERSION[0] >= 2:

    class Disallow1Local(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Reject solely based upon new row (local rejection).',
                'query': DM('Disallow1Local').objects.annotate(
                    new_age=RawSQL('NEW.age', ())
                ).filter(new_age=1)
            }]

    class Disallow1Q(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Q1',
                'query': DM('Disallow1Q').objects.filter(Q(age=1))
            }]

    class Disallow12Q(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Q12',
                'query': DM('Disallow12Q').objects.filter(Q(age=1) | Q(age=2))
            }]

    class Disallow1Annotate(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Annotate1',
                'query': DM('Disallow1Annotate').objects.annotate(
                    disallowed=Value(1, output_field=models.IntegerField())
                ).filter(
                    age=F('disallowed')
                )
            }]

    class Disallow1Subquery(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'All objects must have the same age',
                'query': DM('Disallow1Subquery').objects.annotate(
                    collision=Exists(
                        DM('Disallow1Subquery').objects.filter(
                            age=1
                        )
                    )
                ).filter(
                    collision=True
                )
            }]

    class Disallow13SubquerySlice(AgeModel):
        class Meta:
            constraint_triggers = [{
                'name': 'Slice subquery disallow 13',
                'query': DM('Disallow13SubquerySlice').objects.annotate(
                    max_age=Subquery(
                        DM('Disallow13SubquerySlice').objects.all().values('age').order_by('-age')[:1]
                    )
                ).filter(
                    max_age__gte=1
                )
            }]
