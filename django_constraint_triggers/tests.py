"""The main test module."""
from unittest import skipIf, skip

import django
from django.apps import apps
from django.test import (
    TransactionTestCase,
)
from django.db import models
from django.db.utils import IntegrityError
from django.db import transaction

from parameterized import parameterized, parameterized_class
import django_constraint_triggers


def create(self, model, value):
    model.objects.create(age=value)

def update(self, model, value):
    model.objects.create(age=0)
    model.objects.filter(age=0).update(age=value)

def save(self, model, value):
    model(age=value).save()

def bulk_create(self, model, value):
    model.objects.bulk_create([model(age=value)])

def get_or_create(self, model, value):
    model.objects.get_or_create(age=value)

def update_or_create(self, model, value):
    model.objects.update_or_create(age=value)

# Test that our triggers apply to all methods of insertion / updating
@parameterized_class([
    {"save_method": create},
    {"save_method": update},
    {"save_method": save},
    {"save_method": bulk_create},
    {"save_method": get_or_create},
    {"save_method": update_or_create},
])
class TestAge(TransactionTestCase):

    def disallow(self, model_name, disallow):
        # Load the affected model in
        model = apps.get_model('django_constraint_triggers', model_name)
        # Prepare exception sequence. 1 if we expect exception, 0 if not.
        sequence_len = 3
        sequence = [0] + ([1] * disallow) + ([0] * (sequence_len - disallow))
        for idx, val in enumerate(sequence):
            if val:
                with self.assertRaises(IntegrityError, msg=str(idx)):
                    self.save_method(model, idx)
            else:
                self.save_method(model, idx)

    @parameterized.expand([
        ['AllowAll', 0],
        ['Disallow1', 1],
        ['Disallow12In', 2],
        ['Disallow12Double', 2],
        ['Disallow12Range', 2],
        ['Disallow12Multi', 2],
        ['Disallow13GT', 3],
        ['Disallow13Count', 3],
        ['AllowOnly0', 3],

        ['P2Disallow1Local', 1],
        ['P2Disallow1Q', 1],
        # ['P2Disallow12Q', 2],
        ['P2Disallow1Annotate', 1],
        ['P2Disallow1Subquery', 1],
        ['P2Disallow13SubquerySlice', 3],
    ])
    def test_disallow(self, model, disallow):
        self.disallow(model, disallow)

    @parameterized.expand([
        ['Disallow1Local', 1],
        ['Disallow1Q', 1],
        ['Disallow12Q', 2],
        ['Disallow1Annotate', 1],
        ['Disallow1Subquery', 1],
        ['Disallow13SubquerySlice', 3],
    ])
    @skipIf(django.VERSION[0] == 1, "Model utilized serialized Q objects")
    def test_disallow_django2(self, model, disallow):
        self.disallow(model, disallow)


from django.test import TestCase
from django_constraint_triggers.management.commands.makemigrations import (
    MigrationAutodetector
)
from django.db.migrations.state import ProjectState, ModelState


def gen_m_object(app_label, model_name, trigger_name, pk=1):
    return django_constraint_triggers.models.M(
        app_label=app_label,
        finalized=True,
        model=model_name,
        # Author.objects.filter(pk=1)
        operations=[
            {'args': ('objects',), 'kwargs': {}, 'type': '__getattribute__'},
            {'args': ('filter',), 'kwargs': {}, 'type': '__getattribute__'},
            {'args': (), 'kwargs': {'pk': pk}, 'type': '__call__'}
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

    def gen_model_state(self, app_label, model_name, trigger_name=None, pk=1):
        options_dict = {}
        if trigger_name:
           options_dict = {'constraint_triggers': [{
                'name': trigger_name, 
                'query': gen_m_object(app_label, model_name, trigger_name, pk)
            }]}

        return ModelState(app_label, model_name, [
            ('id', models.AutoField(primary_key=True))
        ], options_dict)

    @parameterized.expand([
        ['test_app', 'Author'],
        ['test_app', 'JohnDeer'],
        ['otherapp', 'Author'],
        ['otherapp', 'JohnDeer'],
    ])
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

    @parameterized.expand([
        ['test_app', 'Author'],
        ['test_app', 'JohnDeer'],
        ['otherapp', 'Author'],
        ['otherapp', 'JohnDeer'],
    ])
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

    @parameterized.expand([
        ['test_app', 'Author', 'id cannot be 1'],
        ['test_app', 'Author', '1'],
        ['test_app', 'JohnDeer', 'id cannot be 1'],
        ['test_app', 'JohnDeer', '1'],
        ['otherapp', 'Author', 'id cannot be 1'],
        ['otherapp', 'Author', '1'],
        ['otherapp', 'JohnDeer', 'id cannot be 1'],
        ['otherapp', 'JohnDeer', '1'],
    ])
    def test_create_model_with_constraint(self, app_label, model_name, trigger_name):
        """Tests autodetection of new models with constraints."""
        model_state = self.gen_model_state(app_label, model_name, trigger_name)
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
        # Trigger
        action = migration.operations[1]
        self.assertEqual(action.__class__.__name__, "AddConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, trigger_name)

    @parameterized.expand([
        ['test_app', 'Author', 'id cannot be 1'],
        ['test_app', 'Author', '1'],
        ['test_app', 'JohnDeer', 'id cannot be 1'],
        ['test_app', 'JohnDeer', '1'],
        ['otherapp', 'Author', 'id cannot be 1'],
        ['otherapp', 'Author', '1'],
        ['otherapp', 'JohnDeer', 'id cannot be 1'],
        ['otherapp', 'JohnDeer', '1'],
    ])
    # TODO: Follow up on this
    @skip("Might not be an issue?")
    def test_delete_model_with_constraint(self, app_label, model_name, trigger_name):
        """Tests autodetection of new models with constraints."""
        model_state = self.gen_model_state(app_label, model_name, trigger_name)
        changes = self.get_changes([model_state], [])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        # Create
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "DeleteModel")
        self.assertEqual(action.name, model_name)
        # Trigger
        action = migration.operations[1]
        self.assertEqual(action.__class__.__name__, "RemoveConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, trigger_name)

    @parameterized.expand([
        ['test_app', 'Author', 'id cannot be 1'],
        ['test_app', 'Author', '1'],
        ['test_app', 'JohnDeer', 'id cannot be 1'],
        ['test_app', 'JohnDeer', '1'],
        ['otherapp', 'Author', 'id cannot be 1'],
        ['otherapp', 'Author', '1'],
        ['otherapp', 'JohnDeer', 'id cannot be 1'],
        ['otherapp', 'JohnDeer', '1'],
    ])
    def test_add_constraint(self, app_label, model_name, trigger_name):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name)
        model_state_after = self.gen_model_state(app_label, model_name, trigger_name)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions
        # Trigger
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "AddConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, trigger_name)

    @parameterized.expand([
        ['test_app', 'Author', 'id cannot be 1'],
        ['test_app', 'Author', '1'],
        ['test_app', 'JohnDeer', 'id cannot be 1'],
        ['test_app', 'JohnDeer', '1'],
        ['otherapp', 'Author', 'id cannot be 1'],
        ['otherapp', 'Author', '1'],
        ['otherapp', 'JohnDeer', 'id cannot be 1'],
        ['otherapp', 'JohnDeer', '1'],
    ])
    def test_remove_constraint(self, app_label, model_name, trigger_name):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name, trigger_name)
        model_state_after = self.gen_model_state(app_label, model_name)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions
        # Trigger
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "RemoveConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, trigger_name)

    @parameterized.expand([
        ['test_app', 'Author', '1', 'id cannot be 1'],
        ['test_app', 'JohnDeer', '1', 'id cannot be 1'],
        ['otherapp', 'Author', '1', 'id cannot be 1'],
        ['otherapp', 'JohnDeer', '1', 'id cannot be 1'],
    ])
    def test_change_constraint_name(self, app_label, model_name, old_trigger_name, new_trigger_name):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name, old_trigger_name)
        model_state_after = self.gen_model_state(app_label, model_name, new_trigger_name)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        # Trigger
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "AddConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, new_trigger_name)
        # Trigger
        action = migration.operations[1]
        self.assertEqual(action.__class__.__name__, "RemoveConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, old_trigger_name)

    @parameterized.expand([
        ['test_app', 'Author', 2],
        ['test_app', 'JohnDeer', 2],
        ['otherapp', 'Author', 2],
        ['otherapp', 'JohnDeer', 2],
    ])
    def test_change_constraint_query(self, app_label, model_name, new_pk):
        """Tests autodetection of new models with constraints."""
        model_state_before = self.gen_model_state(app_label, model_name, '1')
        model_state_after = self.gen_model_state(app_label, model_name, '1', new_pk)
        changes = self.get_changes([model_state_before], [model_state_after])
        # Right number of migrations?
        self.assertEqual(len(changes[app_label]), 1)
        # Right number of actions?
        migration = changes[app_label][0]
        self.assertEqual(len(migration.operations), 2)
        # Right actions
        # Trigger
        action = migration.operations[0]
        self.assertEqual(action.__class__.__name__, "AddConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, '1')
        # Trigger
        action = migration.operations[1]
        self.assertEqual(action.__class__.__name__, "RemoveConstraintTrigger")
        self.assertEqual(action.model_name, model_name.lower())
        self.assertEqual(action.trigger_name, '1')
        # Check the M's are different
        self.assertNotEqual(migration.operations[0].query, migration.operations[1].query)


from django.db import migrations
from django.db import connections
from django.db import connection
from django.db.migrations.migration import Migration

class OperationTests(TransactionTestCase):

    def assertTableExists(self, table, using='default'):
        with connections[using].cursor() as cursor:
            self.assertIn(table, connections[using].introspection.table_names(cursor))

    def assertTableNotExists(self, table, using='default'):
        with connections[using].cursor() as cursor:
            self.assertNotIn(table, connections[using].introspection.table_names(cursor))

    def apply_operations(self, app_label, project_state, operations, atomic=True):
        migration = Migration('name', app_label)
        migration.operations = operations
        with connection.schema_editor(atomic=atomic) as editor:
            return migration.apply(project_state, editor)

    def unapply_operations(self, app_label, project_state, operations, atomic=True):
        migration = Migration('name', app_label)
        migration.operations = operations
        with connection.schema_editor(atomic=atomic) as editor:
            return migration.unapply(project_state, editor)

    def set_up_test_model(
            self, app_label, second_model=False, third_model=False, index=False, multicol_index=False,
            related_model=False, mti_model=False, proxy_model=False, manager_model=False,
            unique_together=False, options=False, db_table=None, index_together=False, constraints=None):
        """
        Creates a test model state and database table.
        """
        # Make the "current" state
        model_options = {
            "swappable": "TEST_SWAP_MODEL",
            "index_together": [["weight", "pink"]] if index_together else [],
            "unique_together": [["pink", "weight"]] if unique_together else [],
        }
        if options:
            model_options["permissions"] = [("can_groom", "Can groom")]
        if db_table:
            model_options["db_table"] = db_table
        operations = [migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=3)),
                ("weight", models.FloatField()),
            ],
            options=model_options,
        )]
        if index:
            operations.append(migrations.AddIndex(
                "Pony",
                models.Index(fields=["pink"], name="pony_pink_idx")
            ))
        if multicol_index:
            operations.append(migrations.AddIndex(
                "Pony",
                models.Index(fields=["pink", "weight"], name="pony_test_idx")
            ))
        if constraints:
            for constraint in constraints:
                operations.append(migrations.AddConstraint(
                    "Pony",
                    constraint,
                ))
        if second_model:
            operations.append(migrations.CreateModel(
                "Stable",
                [
                    ("id", models.AutoField(primary_key=True)),
                ]
            ))
        if third_model:
            operations.append(migrations.CreateModel(
                "Van",
                [
                    ("id", models.AutoField(primary_key=True)),
                ]
            ))
        if related_model:
            operations.append(migrations.CreateModel(
                "Rider",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("pony", models.ForeignKey("Pony", models.CASCADE)),
                    ("friend", models.ForeignKey("self", models.CASCADE))
                ],
            ))
        if mti_model:
            operations.append(migrations.CreateModel(
                "ShetlandPony",
                fields=[
                    ('pony_ptr', models.OneToOneField(
                        'Pony',
                        models.CASCADE,
                        auto_created=True,
                        parent_link=True,
                        primary_key=True,
                        to_field='id',
                        serialize=False,
                    )),
                    ("cuteness", models.IntegerField(default=1)),
                ],
                bases=['%s.Pony' % app_label],
            ))
        if proxy_model:
            operations.append(migrations.CreateModel(
                "ProxyPony",
                fields=[],
                options={"proxy": True},
                bases=['%s.Pony' % app_label],
            ))
        if manager_model:
            operations.append(migrations.CreateModel(
                "Food",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                ],
                managers=[
                    ("food_qs", FoodQuerySet.as_manager()),
                    ("food_mgr", FoodManager("a", "b")),
                    ("food_mgr_kwargs", FoodManager("x", "y", 3, 4)),
                ]
            ))
        return self.apply_operations(app_label, ProjectState(), operations)

    # https://github.com/django/django/blob/master/tests/migrations/test_operations.py#L1664
    def test_constraint_trigger(self):
        app_label = 'test_crmo'
        project_state = self.set_up_test_model(app_label)

        trigger_name = '1'
        model_name = 'Pony'
        m_object = gen_m_object(app_label, model_name, trigger_name)
        operation = django_constraint_triggers.operations.AddConstraintTrigger(
            model_name.lower(), trigger_name, m_object
        )
        self.assertEqual(operation.describe(), "Create constraint trigger {} on model {}".format(
            trigger_name,
            model_name.lower(),
        ))
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        options = new_state.models[app_label, model_name.lower()].options
        self.assertEqual(len(options['constraint_triggers']), 1)
        self.assertEqual(options['constraint_triggers'][0]['name'], trigger_name)
        self.assertEqual(options['constraint_triggers'][0]['query'], m_object)
