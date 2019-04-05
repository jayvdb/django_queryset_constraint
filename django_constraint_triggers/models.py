# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
from django_constraint_triggers.utils import M

DM = partial(M, app_label='django_constraint_triggers')


# TODO: Move these models into test
class AgeModel(models.Model):
    class Meta:
        abstract = True
    age = models.PositiveIntegerField()

class AllowAll(AgeModel):
    pass

# TODO: Changing M to classname results in broken migration
class Disallow1CustomError(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': '1',
            'query': DM('Disallow1CustomError').objects.filter(age=1),
            'error': 'Hello, I am an error message',
        }]

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

class P2Disallow1Local(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Reject solely based upon new row (local rejection).',
            'query': DM('P2Disallow1Local').objects.annotate(
                new_age=partial(RawSQL, 'NEW.age', ())
            ).filter(new_age=1)
        }]

class P2Disallow1Q(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Q1',
            'query': DM('P2Disallow1Q').objects.filter(partial(Q, age=1))
        }]

#class P2Disallow12Q(AgeModel):
#    class Meta:
#        constraint_triggers = [{
#            'name': 'Q12',
#            'query': DM('P2Disallow12Q').objects.filter(partial(Q,age=1) | partial(Q, age=2))
#        }]

class P2Disallow1Annotate(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Annotate1',
            'query': DM('P2Disallow1Annotate').objects.annotate(
                disallowed=partial(Value, 1, output_field=models.IntegerField())
            ).filter(
                age=partial(F, 'disallowed')
            )
        }]

class P2Disallow1Subquery(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'All objects must have the same age',
            'query': DM('P2Disallow1Subquery').objects.annotate(
                collision=partial(Exists,
                    DM('P2Disallow1Subquery').objects.filter(
                        age=1
                    )
                )
            ).filter(
                collision=True
            )
        }]

class P2Disallow13SubquerySlice(AgeModel):
    class Meta:
        constraint_triggers = [{
            'name': 'Slice subquery disallow 13',
            'query': DM('P2Disallow13SubquerySlice').objects.annotate(
                max_age=partial(Subquery,
                    DM('P2Disallow13SubquerySlice').objects.all().values('age').order_by('-age')[:1]
                )
            ).filter(
                max_age__gte=1
            )
        }]
