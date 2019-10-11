from unittest import skip

from django.db import connection, migrations, models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.migration import Migration
from django.db.migrations.state import ModelState, ProjectState
from django.test import TestCase, TransactionTestCase
from parameterized import parameterized

from django_queryset_constraint import M, QuerysetConstraint


def gen_m_object(app_label, model_name, name, pk=1):
    return M(
        operations=[
            {"args": ("objects",), "kwargs": {}, "type": "__getattribute__"},
            {"args": ("filter",), "kwargs": {}, "type": "__getattribute__"},
            {"args": (), "kwargs": {"pk": pk}, "type": "__call__"},
        ]
    )


class AutodetectorTests(TestCase):
    def make_project_state(self, model_states):
        "Shortcut to make ProjectStates from lists of predefined models"
        project_state = ProjectState()
        for model_state in model_states:
            project_state.add_model(model_state.clone())
        return project_state

    def get_changes(self, before_states, after_states, questioner=None):
        return MigrationAutodetector(
            self.make_project_state(before_states),
            self.make_project_state(after_states),
            questioner,
        )._detect_changes()

    def gen_model_state(self, app_label, model_name, name=None, pk=1):
        options_dict = {}
        if name:
            options_dict = {
                "constraints": [
                    QuerysetConstraint(
                        name=name,
                        queryset=gen_m_object(app_label, model_name, name, pk),
                    )
                ]
            }

        return ModelState(
            app_label,
            model_name,
            [("id", models.AutoField(primary_key=True))],
            options_dict,
        )

    @parameterized.expand(
        [
            ["test_app", "Author"],
            ["test_app", "JohnDeer"],
            ["otherapp", "Author"],
            ["otherapp", "JohnDeer"],
        ]
    )
    def test_new_model(self, app_label, model_name):
        """Tests autodetection of new models."""
        model_state = self.gen_model_state(app_label, model_name)
        changes = self.get_changes([], [model_state])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right action?
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "CreateModel")
        self.assertEqual(action.name, model_name)

    @parameterized.expand(
        [
            ["test_app", "Author"],
            ["test_app", "JohnDeer"],
            ["otherapp", "Author"],
            ["otherapp", "JohnDeer"],
        ]
    )
    def test_delete_model(self, app_label, model_name):
        """Tests autodetection of new models."""
        model_state = self.gen_model_state(app_label, model_name)
        changes = self.get_changes([model_state], [])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right action?
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "DeleteModel")
        self.assertEqual(action.name, model_name)

    @parameterized.expand(
        [
            ["test_app", "Author", "id cannot be 1"],
            ["test_app", "Author", "1"],
            ["test_app", "JohnDeer", "id cannot be 1"],
            ["test_app", "JohnDeer", "1"],
            ["otherapp", "Author", "id cannot be 1"],
            ["otherapp", "Author", "1"],
            ["otherapp", "JohnDeer", "id cannot be 1"],
            ["otherapp", "JohnDeer", "1"],
        ]
    )
    def test_create_model_with_constraint(self, app_label, model_name, name):
        """Tests autodetection of new models with constraints."""
        model_state = self.gen_model_state(app_label, model_name, name)
        changes = self.get_changes([], [model_state])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        # Create
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "CreateModel")
        self.assertEqual(action.name, model_name)
        # Constraint
        action = migration.operations[1]
        self.assertEqual(action.__class__.__name__, "AddConstraint")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.constraint.name, name)

    @parameterized.expand(
        [
            ["test_app", "Author", "id cannot be 1"],
            ["test_app", "Author", "1"],
            ["test_app", "JohnDeer", "id cannot be 1"],
            ["test_app", "JohnDeer", "1"],
            ["otherapp", "Author", "id cannot be 1"],
            ["otherapp", "Author", "1"],
            ["otherapp", "JohnDeer", "id cannot be 1"],
            ["otherapp", "JohnDeer", "1"],
        ]
    )
    def test_delete_model_with_constraint(self, app_label, model_name, name):
        """Tests autodetection of new models with constraints."""
        model_state = self.gen_model_state(app_label, model_name, name)
        changes = self.get_changes([model_state], [])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions
        # Create
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "DeleteModel")
        self.assertEqual(action.name, model_name)

    @parameterized.expand(
        [
            ["test_app", "Author", "id cannot be 1"],
            ["test_app", "Author", "1"],
            ["test_app", "JohnDeer", "id cannot be 1"],
            ["test_app", "JohnDeer", "1"],
            ["otherapp", "Author", "id cannot be 1"],
            ["otherapp", "Author", "1"],
            ["otherapp", "JohnDeer", "id cannot be 1"],
            ["otherapp", "JohnDeer", "1"],
        ]
    )
    def test_add_constraint(self, app_label, model_name, name):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name)
        model_state_after = self.gen_model_state(app_label, model_name, name)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions
        # Constraint
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "AddConstraint")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.constraint.name, name)

    @parameterized.expand(
        [
            ["test_app", "Author", "id cannot be 1"],
            ["test_app", "Author", "1"],
            ["test_app", "JohnDeer", "id cannot be 1"],
            ["test_app", "JohnDeer", "1"],
            ["otherapp", "Author", "id cannot be 1"],
            ["otherapp", "Author", "1"],
            ["otherapp", "JohnDeer", "id cannot be 1"],
            ["otherapp", "JohnDeer", "1"],
        ]
    )
    def test_remove_constraint(self, app_label, model_name, name):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name, name)
        model_state_after = self.gen_model_state(app_label, model_name)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions
        # Constraint
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "RemoveConstraint")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.name, name)

    @parameterized.expand(
        [
            ["test_app", "Author", "1", "id cannot be 1"],
            ["test_app", "JohnDeer", "1", "id cannot be 1"],
            ["otherapp", "Author", "1", "id cannot be 1"],
            ["otherapp", "JohnDeer", "1", "id cannot be 1"],
        ]
    )
    def test_change_constraint_name(
        self, app_label, model_name, old_name, new_name
    ):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(
            app_label, model_name, old_name
        )
        model_state_after = self.gen_model_state(
            app_label, model_name, new_name
        )
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        remove_action = next(
            (
                x
                for x in migration.operations
                if x.__class__.__name__ == "RemoveConstraint"
            )
        )
        add_action = next(
            (
                x
                for x in migration.operations
                if x.__class__.__name__ == "AddConstraint"
            )
        )
        # Constraint
        self.assertEqual(remove_action.model_name, model_name.lower())
        self.assertEqual(remove_action.name, old_name)
        # Constraint
        self.assertEqual(add_action.model_name, model_name.lower())
        self.assertEqual(add_action.constraint.name, new_name)

    @parameterized.expand(
        [
            ["test_app", "Author", 2],
            ["test_app", "JohnDeer", 2],
            ["otherapp", "Author", 2],
            ["otherapp", "JohnDeer", 2],
        ]
    )
    def test_change_constraint_query(self, app_label, model_name, new_pk):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name, "1")
        model_state_after = self.gen_model_state(
            app_label, model_name, "1", new_pk
        )
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        remove_action = next(
            (
                x
                for x in migration.operations
                if x.__class__.__name__ == "RemoveConstraint"
            )
        )
        add_action = next(
            (
                x
                for x in migration.operations
                if x.__class__.__name__ == "AddConstraint"
            )
        )
        # Constraint
        self.assertEqual(remove_action.model_name, model_name.lower())
        self.assertEqual(remove_action.name, "1")
        self.assertFalse(hasattr(remove_action, "constraint"))
        self.assertFalse(hasattr(remove_action, "m_object"))
        # Constraint
        self.assertEqual(add_action.model_name, model_name.lower())
        self.assertEqual(add_action.constraint.name, "1")
        self.assertTrue(hasattr(add_action, "constraint"))
        self.assertTrue(hasattr(add_action.constraint, "m_object"))


class OperationTests(TransactionTestCase):
    def apply_operations(
        self, app_label, project_state, operations, atomic=True
    ):
        migration = Migration("name", app_label)
        migration.operations = operations
        with connection.schema_editor(atomic=atomic) as editor:
            return migration.apply(project_state, editor)

    def set_up_test_model(self, app_label):
        """
        Creates a test model state and database table.
        """
        # Make the "current" state
        model_options = {"swappable": "TEST_SWAP_MODEL"}
        operations = [
            migrations.CreateModel(
                "Pony",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("pink", models.IntegerField(default=3)),
                    ("weight", models.FloatField()),
                ],
                options=model_options,
            )
        ]
        return self.apply_operations(app_label, ProjectState(), operations)

    # https://github.com/django/django/blob/master/tests/migrations/test_operations.py#L1664
    def test_constraint_trigger(self):
        app_label = "test_crmo"
        project_state = self.set_up_test_model(app_label)

        name = "1"
        model_name = "Pony"
        m_object = gen_m_object(app_label, model_name, name)
        operation = migrations.AddConstraint(
            model_name=model_name.lower(),
            constraint=QuerysetConstraint(name=name, queryset=m_object),
        )
        self.assertEqual(
            operation.describe(),
            "Create constraint {} on model {}".format(name, model_name.lower()),
        )
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        options = new_state.models[app_label, model_name.lower()].options
        self.assertEqual(len(options["constraints"]), 1)
        self.assertEqual(options["constraints"][0].name, name)
        self.assertEqual(options["constraints"][0].m_object, m_object)
