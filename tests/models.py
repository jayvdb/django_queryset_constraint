"""Test specific models."""

from django.db import models


class SignalUser(models.Model):
    # We use these two data fields in our tests
    username = models.CharField(max_length=100, unique=True)
    last_name = models.CharField(max_length=100)
