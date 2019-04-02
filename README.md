Django Constraint Triggers
==========================

[![Build Status](https://travis-ci.org/magenta-aps/django_constraint_triggers.svg?branch=master)](https://travis-ci.org/magenta-aps/django_constraint_triggers)

This library enables one to write reliable data invariants, by compiling Django
Querysets to database insert/update triggers, via. the migration system.

Motivation
==========
Django has a built-in signal system, which emits signals on various events, for
instance model creations, updates and deletions. However these signals are not
emmited for queryset operations, and as such cannot be used to maintain data
invariants.

An attempt to ratify this was made with the [Django Queryset Signals](https://github.com/magenta-aps/django-queryset-signals) library.
While this library comes closer to a reliable solution, it does not succeed,
as it is stil possible to break the data invariants by accessing the database
directly.

Database Constraint Triggers will effectively protect against all scenarios.

Installation
============
```
pip install --index-url https://test.pypi.org/simple/ django_constraint_triggers
```

Usage
=====

- Add the `django_constraint_triggers` app to `INSTALLED_APPS`:

```
# settings.py
INSTALLED_APPS = {
    'django_constraint_triggers',
    ...
}
```

*Note: This should be done **before** any apps that will be checked*

- Add `constraint_triggers` to the Meta class of the models to checked:

```
# models.py
class MyCheckedModel(models.Model):
    ...
    class Meta:
        constraint_triggers = [{
            'name': 'Age > 12',
            'query': M('MyCheckedModel', app_label='test').objects.filter(
                age__gt=12
            )
        }]
    age = models.PositiveIntegerField()
```

*Note: The above is clearly a toy example, and could be achieved using
Django's [CheckConstraint](https://docs.djangoproject.com/en/dev/ref/models/constraints/#checkconstraint)
(> 2.0) or even using a [MinValueValidator](https://docs.djangoproject.com/en/dev/ref/validators/#minvaluevalidator)
on the [PositiveIntegerField](https://docs.djangoproject.com/en/dev/ref/models/fields/#positiveintegerfield) itself.*

- Make migrations: `python manage.py makemigrations`
- Run migrations: `python manage.py migrate`

*Note: Complex triggers introduce performance overhead.*

Support Matrix
==============
This app supports the following combinations of Django and Python:

| Django     | Python                  |
| ---------- | ----------------------- |
| 1.11 (`x`) | 2.7, 3.4, 3.5, 3.6, 3.7 |
| 2.0        | 3.4, 3.5, 3.6, 3.7      |
| 2.1        | 3.5, 3.6, 3.7           |

`x`: Functionality is limited on 1.11, as this version does not support
serialization of queryset expressions, such as `Q` and `F` objects. This can
potentially be ratified using partials inside the `M` object.

Caveats
=======
This library relies on monkey patching several Django builtins;

- `django.db.models.options`
- `django.db.migrations.state`

To support the new Meta class option; `constraint_triggers`.

- `django.core.management.commands.makemigrations.MigrationAutodetector`

To replace the `MigrationAutodetector`, such that changes to the new Meta class
field can automatically generate corresponding migration files.


The library may thus conflict with other libraries that monkey patch the same
classes / arrays.
