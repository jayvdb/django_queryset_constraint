from django.db import connection
from django.db.models.constraints import BaseConstraint

from django_queryset_constraint.utils import M


class QuerysetConstraint(BaseConstraint):
    def __init__(self, queryset, name):
        super().__init__(name)
        if not isinstance(queryset, M):
            raise ValueError("'queryset' should be an M object")
        self.m_object = queryset

    def _generate_names(self, table):
        # We cannot include trigger_name + table as it may be too long.
        # Thus we need to truncate. Postgres limits us to 63 characters.
        # We know our prefix is 13 characters, thus we need to limit to 50.
        # To be safe, we will limit to 40.
        hashy = hex(hash(self.name + table))[3 : 40 + 3]
        # Prepare function and trigger name
        function_name = "__".join(["dct", "func", hashy]) + "()"
        trigger_name = "__".join(["dct", "trig", hashy])
        return function_name, trigger_name

    def _install_trigger(self, schema_editor, model, defer=True, error=None):
        table = model._meta.db_table
        function_name, trigger_name = self._generate_names(table)
        app_label = model._meta.app_label
        model_name = model._meta.object_name

        # No error message - Default to 'Invariant broken'
        if error is None:
            error = "Invariant broken: " + self.name

        # Run through all operations to generate our queryset
        result = self.m_object.construct_queryset(app_label, model_name)
        # Generate query from result
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
            function_name, query.decode(), error
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
            "DEFERRABLE INITIALLY DEFERRED" if defer else "",
            function_name,
        )
        return schema_editor.execute(function + trigger)

    def _remove_trigger(self, schema_editor, model):
        table = model._meta.db_table
        function_name, trigger_name = self._generate_names(table)
        # Remove trigger
        return schema_editor.execute(
            "DROP TRIGGER {} ON {};".format(trigger_name, table)
            + "DROP FUNCTION {};".format(function_name)
        )

    def constraint_sql(self, model, schema_editor):
        return ""

    def create_sql(self, model, schema_editor):
        return self._install_trigger(schema_editor, model=model)

    def remove_sql(self, model, schema_editor):
        return self._remove_trigger(schema_editor, model=model)

    def __eq__(self, other):
        if not isinstance(other, QuerysetConstraint):
            return NotImplemented
        return self.name == other.name and self.m_object == other.m_object

    def __str__(self):
        return self.name + " : " + str(self.m_object)

    def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        return path, [], {"name": self.name, "queryset": self.m_object}
