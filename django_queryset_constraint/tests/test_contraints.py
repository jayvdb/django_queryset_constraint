from django.test import TestCase

from django_queryset_constraint.constraints import QuerysetConstraint
from django_queryset_constraint.models import AllowAll


class QuerysetConstraintTests(TestCase):
    def test_equality(self):
        c1 = QuerysetConstraint(AllowAll.objects.all(), name='n1')
        c2 = QuerysetConstraint(AllowAll.objects.all(), name='n2')
        c3 = QuerysetConstraint(AllowAll.objects.filter(age=42), name='n2')
        c4 = QuerysetConstraint(AllowAll.objects.filter(age=42), name='n2')
        with self.assertNumQueries(0):
            self.assertNotEqual(c1, self)
        with self.assertNumQueries(0):
            self.assertNotEqual(c1, c2)
        with self.assertNumQueries(0):
            self.assertNotEqual(c2, c3)
        with self.assertNumQueries(0):
            self.assertNotEqual(c2, c3)
        with self.assertNumQueries(0):
            self.assertEqual(c3, c4)
