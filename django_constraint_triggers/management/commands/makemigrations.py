try:
    from unittest.mock import patch
except ImportError:  # Handle python 2.7
    from mock import patch

from itertools import chain

from django.core.management.commands import makemigrations
from django.db.migrations import autodetector, state

from django_constraint_triggers.operations import (
    AddConstraintTrigger,
    RemoveConstraintTrigger
)

# HACK: add audit_trigger to available Meta options
state.DEFAULT_NAMES = state.DEFAULT_NAMES + (
    'constraint_triggers',
)


class MigrationAutodetector(autodetector.MigrationAutodetector):

    def generate_altered_db_table(self):
        super(MigrationAutodetector, self).generate_altered_db_table()
        # Install constraint triggers
        self.altered_constraint_triggers = {}
        self.create_altered_constraint_triggers()
        self.generate_added_constraint_triggers()
        self.generate_removed_constraint_triggers()

    def generate_created_models(self):
        super(MigrationAutodetector, self).generate_created_models()
        # Install constraint triggers
        if isinstance(self.old_model_keys, list):  # Handle python 2.7
            old_keys = self.old_model_keys + self.old_unmanaged_keys
        elif isistance(self.old_model_keys, set):
            old_keys = self.old_model_keys | self.old_unmanaged_keys

        added_models = [x for x in self.new_model_keys if x not in old_keys]
        added_unmanaged_models = [x for x in self.new_unmanaged_keys if x not in old_keys]
        all_added_models = chain(
            sorted(added_models, key=self.swappable_first_key, reverse=True),
            sorted(added_unmanaged_models, key=self.swappable_first_key, reverse=True)
        )
        option_name = AddConstraintTrigger.option_name
        for app_label, model_name in all_added_models:
            model_state = self.to_state.models[app_label, model_name]
            constraints = model_state.options.get(option_name, [])
            for trigger in constraints:
                self.add_operation(
                    app_label,
                    AddConstraintTrigger(
                        model_name=model_name,
                        trigger_name=trigger['name'],
                        query=trigger['query'],
                    )
                )

    def create_altered_constraint_triggers(self):
        option_name = AddConstraintTrigger.option_name
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get((app_label, model_name), model_name)
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]

            # Get old constraints as array
            old_constraints = old_model_state.options.get(option_name, [])
            new_constraints = new_model_state.options.get(option_name, [])

            # Figure out which constraints were added / removed
            add_constraints = [c for c in new_constraints if c not in old_constraints]
            rem_constraints = [c for c in old_constraints if c not in new_constraints]

            self.altered_constraint_triggers.update({
                (app_label, model_name): {
                    'added_constraint_triggers': add_constraints,
                    'removed_constraint_triggers': rem_constraints,
                }
            })

    def generate_added_constraint_triggers(self):
        for (app_label, model_name), alt_constraints in self.altered_constraint_triggers.items():
            for trigger in alt_constraints['added_constraint_triggers']:
                self.add_operation(
                    app_label,
                    AddConstraintTrigger(
                        model_name=model_name,
                        trigger_name=trigger['name'],
                        query=trigger['query'],
                    )
                )

    def generate_removed_constraint_triggers(self):
        for (app_label, model_name), alt_constraints in self.altered_constraint_triggers.items():
            for trigger in alt_constraints['removed_constraint_triggers']:
                self.add_operation(
                    app_label,
                    RemoveConstraintTrigger(
                        model_name=model_name,
                        trigger_name=trigger['name'],
                        query=trigger['query'],
                    )
                )


class Command(makemigrations.Command):
    """
    Since the MigrationAutodetector isn't extensible, patch the instance with
    our custom autodetector.
    """

    # TODO: Avoid patching, may need an upstream change to:
    # https://github.com/django/django/blob/master/django/core/management/commands/makemigrations.py#L140
    @patch(
        'django.core.management.commands.makemigrations.MigrationAutodetector',
        new=MigrationAutodetector,
    )
    def handle(self, *app_labels, **options):
        return super(Command, self).handle(*app_labels, **options)
