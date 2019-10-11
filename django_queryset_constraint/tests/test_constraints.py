from django.test import TestCase
from parameterized import parameterized

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

    def test_no_constraint_sql(self):
        self.assertEqual(
            QuerysetConstraint(M().objects.all(), name="n1").constraint_sql(None, None),
            ""
        )

    @parameterized.expand(
        [
            ["n1", M().objects.all()],
            ["n2", M().objects.all()],
            ["n2", M().objects.filter(age=42)],
            ["n2", M().objects.filter(age=42)],
        ]
    )
    def test_deconstruct(self, name, m_object):
        constraint = QuerysetConstraint(m_object, name)
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django_queryset_constraint.constraints.QuerysetConstraint")
        self.assertEqual(args, [])
        self.assertEqual(kwargs['name'], name)
        self.assertEqual(kwargs['queryset'], m_object)
        reconstructed = QuerysetConstraint(*args, **kwargs)
        self.assertEqual(constraint, reconstructed)
        self.assertEqual(str(constraint), str(reconstructed))
