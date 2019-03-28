# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-28 14:36
from __future__ import unicode_literals

from django.db import migrations
import django_constraint_triggers.models
import django_constraint_triggers.operations


class Migration(migrations.Migration):

    dependencies = [
        ('django_constraint_triggers', '0003_auto_20190328_1432'),
    ]

    operations = [
        django_constraint_triggers.operations.RemoveConstraintTrigger(
            model_name='disallow12multi',
            trigger_name='1',
            query=django_constraint_triggers.models.M(app_label=None, model='Disallow12Multi', operations=[{'name': b'objects', 'type': '__getattribute__'}, {'name': b'filter', 'type': '__getattribute__'}, {'args': (), 'kwargs': {b'age': 1}, 'type': '__call__'}]),
        ),
        django_constraint_triggers.operations.RemoveConstraintTrigger(
            model_name='disallow12multi',
            trigger_name='2',
            query=django_constraint_triggers.models.M(app_label=None, model='Disallow12Multi', operations=[{'name': b'objects', 'type': '__getattribute__'}, {'name': b'filter', 'type': '__getattribute__'}, {'args': (), 'kwargs': {b'age': 2}, 'type': '__call__'}]),
        ),
        django_constraint_triggers.operations.RemoveConstraintTrigger(
            model_name='disallow13gt',
            trigger_name='GTE1',
            query=django_constraint_triggers.models.M(app_label=None, model='Disallow13GT', operations=[{'name': b'objects', 'type': '__getattribute__'}, {'name': b'filter', 'type': '__getattribute__'}, {'args': (), 'kwargs': {b'age__gte': 1}, 'type': '__call__'}]),
        ),
    ]