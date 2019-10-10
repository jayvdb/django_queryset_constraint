from django.db import connection
from django.db.models.constraints import BaseConstraint

class QuerysetConstraint(BaseConstraint):
    def __init__(self, queryset, name):
        self.queryset = queryset
        super().__init__(name)

    def _generate_names(self, table):
        # We cannot include trigger_name + table as it may be too long.
        # Thus we need to truncate. Postgres limits us to 63 characters.
        # We know our prefix is 13 characters, thus we need to limit to 50.
        # To be safe, we will limit to 40.
        hashy = hex(hash(self.name + table))[3:40+3]
        # Prepare function and trigger name
        function_name = '__'.join(['dct', 'func', hashy]) + '()'
        trigger_name = '__'.join(['dct', 'trig', hashy])
        return function_name, trigger_name

    def _install_trigger(self, schema_editor, model, defer=True, error=None):
        table = model._meta.db_table
        app_label = model._meta.app_label
        model_name = model._meta.object_name

        function_name, trigger_name = self._generate_names(table)

        # No error message - Default to 'Invariant broken'
        if error is None:
            error = 'Invariant broken'

        # Run through all operations to generate our queryset
        self.queryset.app_label = self.queryset.app_label or app_label
        self.queryset.model_name = self.queryset.model_name or model_name
        result = self.queryset.replay()
        # Generate query from queryset
        cursor = connection.cursor()
        sql, sql_params = result.query.get_compiler(using=result.db).as_sql()
        query = cursor.mogrify(sql, sql_params)

        # Install function
        function = """
            CREATE FUNCTION {}
            RETURNS TRIGGER
            AS $$
            BEGIN
                IF EXISTS (
                    {}
                ) THEN
                    RAISE check_violation USING MESSAGE = '{}';
                END IF;
                RETURN NULL;
            END
            $$ LANGUAGE plpgsql;
        """.format(
            function_name,
            query.decode(),
            error,
        )
        # Install trigger
        trigger = """
            CREATE CONSTRAINT TRIGGER {}
            AFTER INSERT OR UPDATE ON {}
            {}
            FOR EACH ROW
                EXECUTE PROCEDURE {};
        """.format(
            trigger_name,
            table,
            'DEFERRABLE INITIALLY DEFERRED' if defer else '',
            function_name,
        )
        return schema_editor.execute(function + trigger)


    def _remove_trigger(self, schema_editor, model):
        table = model._meta.db_table
        function_name, trigger_name = self._generate_names(table)
        # Remove trigger
        return schema_editor.execute(
            "DROP TRIGGER {} ON {};".format(trigger_name, table) +
            "DROP FUNCTION {};".format(function_name)
        )

    def constraint_sql(self, model, schema_editor):
        return ""

    def create_sql(self, model, schema_editor):
        return self._install_trigger(
            schema_editor, 
            model=model,
        )

    def remove_sql(self, model, schema_editor):
        return self._remove_trigger(
            schema_editor, 
            model=model,
        )

    def __eq__(self, other):
        if not isinstance(other, QuerysetConstraint):
            return NotImplemented
        return (
            self.name == other.name and
            str(self.queryset.query) == str(other.queryset.query)
        )

    def deconstruct(self):
        path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        path, args, kwargs = (path, (), {'name': self.name})
        kwargs['queryset'] = self.queryset
        return path, args, kwargs



