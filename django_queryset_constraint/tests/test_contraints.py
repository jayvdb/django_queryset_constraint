from django.test import TestCase

from django_queryset_constraint import M, QuerysetConstraint
from django_queryset_constraint.models import Pizza


class QuerysetConstraintTests(TestCase):
    def test_equality(self):
        c1 = QuerysetConstraint(M().objects.all(), name="n1")
        c2 = QuerysetConstraint(M().objects.all(), name="n2")
        c3 = QuerysetConstraint(M().objects.filter(age=42), name="n2")
        c4 = QuerysetConstraint(M().objects.filter(age=42), name="n2")
        with self.assertNumQueries(0):
            self.assertNotEqual(c1, self)
            self.assertNotEqual(c2, self)
            self.assertNotEqual(c3, self)
            self.assertNotEqual(c4, self)

            self.assertNotEqual(c1, c2)
            self.assertNotEqual(c1, c3)
            self.assertNotEqual(c1, c4)

            self.assertNotEqual(c2, c3)
            self.assertNotEqual(c2, c4)

            self.assertEqual(c3, c4)

    def test_cannot_provide_real_queryset(self):
        with self.assertRaises(ValueError):
            QuerysetConstraint(Pizza.objects.all(), name="pizza")
