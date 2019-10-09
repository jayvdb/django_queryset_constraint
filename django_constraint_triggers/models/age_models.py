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


# TODO: Move these models into test
class AgeModel(models.Model):
    """Abstract model used as base for all test models."""
    class Meta:
        abstract = True
    age = models.PositiveIntegerField()


class AllowAll(AgeModel):
    """No constraints."""
    pass


class Disallow1CC(AgeModel):
    """CheckConstraint against single value."""
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age=1',
                check=~Q(age=1),
            )
        ]


class Disallow1QC(AgeModel):
    """QuerysetConstraint against single value."""
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1',
                queryset=M().objects.filter(age=1),
            )
        ]


class Disallow1ViaQQC(AgeModel):
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via Q',
                queryset=M().objects.filter(Q(age=1)),
            )
        ]


class Disallow1TriggerNewQC(AgeModel):
    """QuerysetConstraint against single value from Trigger.NEW."""
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via trigger NEW',
                queryset=M().objects.annotate(
                    new_age=RawSQL('NEW.age', ())
                ).filter(new_age=1)
            )
        ]


class Disallow12InCC(AgeModel):
    """CheckConstraint against value in list."""
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age in list',
                check=~Q(age__in=[1,2]),
            )
        ]


class Disallow12InQC(AgeModel):
    """Constraint against value in list."""
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age in list',
                queryset=M().objects.filter(age__in=[1,2]),
            )
        ]


class Disallow12ViaQQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age in or via Q',
                queryset=M().objects.filter(Q(age=1) | Q(age=2)),
            )
        ]


class Disallow12OneFilterCC(AgeModel):
    """CheckConstraint against value in list."""
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age ONE filter',
                check=~(Q(age__gte=1, age__lte=2)),
            )
        ]


class Disallow12OneFilterQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age ONE filter',
                queryset=M().objects.filter(age__gte=1, age__lte=2)
            )
        ]


class Disallow12AndFilterCC(AgeModel):
    """CheckConstraint against value in list."""
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age AND filter',
                check=~(Q(age__gte=1) & Q(age__lte=2)),
            )
        ]


class Disallow12AndFilterQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age AND filter',
                queryset=M().objects.filter(age__gte=1).filter(age__lte=2)
            )
        ]


class Disallow12MultiFilterCC(AgeModel):
    """CheckConstraint against value in list."""
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age Multi1 filter',
                check=~Q(age=1),
            ),
            models.CheckConstraint(
                name='CC: Disallow age Multi2 filter',
                check=~Q(age=2),
            )
        ]


class Disallow12MultiFilterQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age Multi1 filter',
                queryset=M().objects.filter(age=1)
            ),
            QuerysetConstraint(
                name='QC: Disallow age Multi2 filter',
                queryset=M().objects.filter(age=2)
            )
        ]


class Disallow12MultiFilterMixed(AgeModel):
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age MultiMixed filter',
                check=~Q(age=1),
            ),
            QuerysetConstraint(
                name='QC: Disallow age MultiMixed filter',
                queryset=M().objects.filter(age=2)
            )
        ]


class Disallow12RangeCC(AgeModel):
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Disallow age range filter',
                check=~Q(age__range=(1,2)),
            )
        ]


class Disallow12RangeQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age range filter',
                queryset=M().objects.filter(age__range=(1,2))
            )
        ]


class AllowOnly0CC(AgeModel):
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='CC: Allow only 0',
                check=Q(age=0),
            )
        ]


class AllowOnly0QC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Allow only 0',
                queryset=M().objects.exclude(age=0)
            )
        ]


#-----------------------------------#
# Not possible with CheckConstraint #
#-----------------------------------#
class AllowOnly1ObjectQC(AgeModel):
    class Meta:
        constraints = [
            # Allow only 1 object in table (by using offset 1)
            QuerysetConstraint(
                name='QC: Allow only 1 object',
                queryset=M().objects.all()[1:]
            )
        ]


class Disallow1AnnotateQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via annotation',
                queryset=M().objects.annotate(
                    disallowed=Value(1, output_field=models.IntegerField())
                ).filter(
                    age=F('disallowed')
                )
            )
        ]


class Disallow1SubqueryQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via subquery',
                queryset=M().objects.annotate(
                    collision=Exists(
                        M().objects.filter(
                            age=1
                        )
                    )
                ).filter(
                    collision=True
                )
            )
        ]


class Disallow13SubquerySliceQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age>0 via subquery slice',
                queryset=M().objects.annotate(
                    max_age=Subquery(
                        M().objects.all().values('age').order_by('-age')[:1]
                    )
                ).filter(
                    max_age__gte=1
                )
            )
        ]


class Disallow13WhenQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age>0 via When',
                queryset=M().objects.annotate(
                    block=Case(
                        When(age=1, then=F('age')),
                        When(age__gt=1, then=Value(1)),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    )
                ).filter(
                    block=1
                )
            )
        ]


def generate_subquery(layers):
    """Generate a queryset with 'layers' subqueries."""
    inner_queryset = M().objects.filter(
        age=1
    )
    return_queryset = inner_queryset
    for _ in range(layers):
        return_queryset = M().objects.annotate(
            collision=Exists(
                return_queryset
            )
        ).filter(
            collision=True
        )
    return return_queryset


class Disallow1SubqueryWith1SubqueryQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via subquery with 1 subquery',
                queryset=generate_subquery(1)
            )
        ]


class Disallow1SubqueryWith2SubqueryQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via subquery with 2 subqueries',
                queryset=generate_subquery(2)
            )
        ]


class Disallow1SubqueryWith3SubqueryQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via subquery with 3 subqueries',
                queryset=generate_subquery(3)
            )
        ]


class Disallow1SubqueryWith7SubqueryQC(AgeModel):
    class Meta:
        constraints = [
            QuerysetConstraint(
                name='QC: Disallow age=1 via subquery with 7 subqueries',
                queryset=generate_subquery(7)
            )
        ]
