from django.db.migrations.operations.models import IndexOperation
from django.apps import apps


def generate_names(trigger_name, table):
    # We cannot include trigger_name + table as it may be too long.
    # Thus we need to truncate. Postgres limits us to 63 characters.
    # We know our prefix is 13 characters, thus we need to limit to 50.
    # To be safe, we will limit to 40.
    hashy = hex(hash(trigger_name + table))[3:40+3]
    # Prepare function and trigger name
    function_name = '__'.join(['dct', 'func', hashy]) + '()'
    trigger_name = '__'.join(['dct', 'trig', hashy])
    return function_name, trigger_name


def install_trigger(schema_editor, trig_name, trig_type, query, model, error=None):
    table = model._meta.db_table
    function_name, trigger_name = generate_names(trig_name, table)

    # No error message - Default to 'Invariant broken'
    if error is None:
        error = 'Invariant broken'

    # No model - Assume the one we are bound to
    model_name = query.model or model.__name__

    # No app label - Assume it is the same as model
    app_label = query.app_label
    if app_label is None:
        app_label = model._meta.app_label

    # Load the affected model in
    model = apps.get_model(app_label, model_name)
    # Run through all operations to generate our queryset
    result = model
    for operation in query.operations:
        if operation['type'] == '__getattribute__':
            result = getattr(result, str(operation['name']))
        elif operation['type'] == '__call__':
            result = result(*operation['args'], **operation['kwargs'])
        else:
            raise Exception("Unknown operation!")
    # Generate query from queryset
    query = str(result.query)

    # Install function
    function = """
        CREATE FUNCTION {}
        RETURNS TRIGGER
        AS $$
        BEGIN
            IF EXISTS (
                {}
            ) THEN
                RAISE EXCEPTION '{}';
            END IF;
            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
    """.format(
        function_name,
        query,
        error,
    )
    schema_editor.execute(function)
    # Install trigger
    trigger = """
        CREATE TRIGGER {}
        AFTER INSERT OR UPDATE ON {}
        FOR EACH {}
            EXECUTE PROCEDURE {};
    """.format(
        trigger_name,
        table,
        trig_type,
        function_name,
    )
    schema_editor.execute(trigger)


def remove_trigger(schema_editor, trig_name, model):
    table = model._meta.db_table
    function_name, trigger_name = generate_names(trig_name, table)
    # Remove trigger
    schema_editor.execute(
        "DROP TRIGGER {} ON {};".format(trigger_name, table)
    )
    # Install trigger
    schema_editor.execute(
        "DROP FUNCTION {};".format(function_name)
    )


class AddConstraintTrigger(IndexOperation):
    option_name = 'constraint_triggers'

    # TODO: Support both ROW and statement triggers
    def __init__(self, model_name, trigger_name, query): #, trigger_type=None):
        self.model_name = model_name
        self.trigger_name = trigger_name
        self.query = query
        # TODO: Statement as default?
        # self.trigger_type = trigger_type or "ROW"
        self.trigger_type = "ROW"

    def state_forwards(self, app_label, state):
        model_state = state.models[app_label, self.model_name_lower]
        if self.option_name not in model_state.options:
            model_state.options[self.option_name] = []
        model_state.options[self.option_name].append(
            {
                u'name': self.trigger_name,
                u'query': self.query,
            }
        )
        state.reload_model(app_label, self.model_name_lower, delay=True)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        if self.allow_migrate_model(schema_editor.connection.alias, model):
            install_trigger(schema_editor, self.trigger_name,
                            self.trigger_type, self.query, model)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        if self.allow_migrate_model(schema_editor.connection.alias, model):
            remove_trigger(schema_editor, self.trigger_name, model)

    def deconstruct(self):
        return self.__class__.__name__, [], {
            'model_name': self.model_name,
            'trigger_name': self.trigger_name,
            'query': self.query,
        }

    def describe(self):
        return "Create constraint trigger {} on model {}".format(
            self.trigger_name,
            self.model_name
        )


class RemoveConstraintTrigger(AddConstraintTrigger):

    def state_forwards(self, app_label, state):
        model_state = state.models[app_label, self.model_name_lower]
        constraints = model_state.options[self.option_name]
        model_state.options[self.option_name] = [c for c in constraints if c['name'] != self.trigger_name]
        state.reload_model(app_label, self.model_name_lower, delay=True)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        super(RemoveConstraintTrigger, self).database_backwards(
            app_label, schema_editor, from_state, to_state,
        )

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        super(RemoveConstraintTrigger, self).database_forwards(
            app_label, schema_editor, from_state, to_state,
        )

    def describe(self):
        return "Remove constraint trigger {} from model {}".format(
            self.trigger_name,
            self.model_name
        )
