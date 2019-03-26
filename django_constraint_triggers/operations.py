from django.db.migrations.operations.models import IndexOperation


def generate_names(trigger_name, table):
    # Prepare function and trigger name
    prefix = ['dct', table]
    function_name = '__'.join(prefix + ['func', trigger_name]) + '()'
    trigger_name = '__'.join(prefix + ['trig', trigger_name])
    return function_name, trigger_name


def install_trigger(schema_editor, trig_name, trig_type, query, error, table):
    function_name, trigger_name = generate_names(trig_name, table)
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


def remove_trigger(schema_editor, trig_name, table):
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
                u'name': unicode(self.trigger_name),
                # u'type': unicode(self.trigger_type),
                u'query': unicode(self.query),
            }
        )
        state.reload_model(app_label, self.model_name_lower, delay=True)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        table = model._meta.db_table
        if self.allow_migrate_model(schema_editor.connection.alias, model):
            install_trigger(schema_editor, self.trigger_name,
                            self.trigger_type, self.query, 'Invariant broken',
                            table)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        table = model._meta.db_table
        if self.allow_migrate_model(schema_editor.connection.alias, model):
            remove_trigger(schema_editor, self.trigger_name, table)

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
