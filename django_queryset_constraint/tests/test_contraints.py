from django.test import SimpleTestCase

from django_queryset_constraint.constraints import QuerysetConstraint
from django_queryset_constraint.models import AgeModel


class QuerysetConstraintTests(SimpleTestCase):
    def test_equality(self):
        c1 = QuerysetConstraint(AgeModel.objects.all(), name='n1')
        c2 = QuerysetConstraint(AgeModel.objects.all(), name='n2')
        c3 = QuerysetConstraint(AgeModel.objects.filter(age=42), name='n3')
        c4 = QuerysetConstraint(AgeModel.objects.filter(age=42), name='n3')
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
