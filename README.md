Django Constraint Triggers
==========================

This app sets up postgres triggers to check invariants.

Installation
============
```
pip install django_constraint_triggers
```
(Eventually)


Usage
=====

- Add the `django_constraint_triggers` app to `INSTALLED_APPS` *before* any apps that will be checked:

```
# settings.py
INSTALLED_APPS = {
    'django.contrib.postgres',
    'django_constraint_triggers',
    ...
}
```

- Add `constraint_triggers` to the Model Meta options of the models that will be checked:

```
# models.py
class MyCheckedModel(models.Model):
    ...
    class Meta:
        def constraint_triggers():
            # Check that new entries are always older than old ones
            return [
                {
                    'name': 'Check older',
                    'query': MyCheckedModel.objects.filter(
                        age__gte=RawSQL('NEW.age', ())
                    )
                },
            ]

    age = models.PositiveIntegerField()
```

- Make migrations: `python manage.py makemigrations`
- Run migrations: `python manage.py migrate`

Triggers introduce performance overhead. 
