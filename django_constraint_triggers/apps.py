# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models import options

# XXX: Hack to add constraint_triggers to the available Meta options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'constraint_triggers',
)


class DjangoConstraintTriggersConfig(AppConfig):
    name = 'django_constraint_triggers'
