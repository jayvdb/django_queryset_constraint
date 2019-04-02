#!/bin/bash

rm -f django_constraint_triggers/migrations/0*
rm -rf build/ dist/ django_constraint_triggers.egg-inf
python3 setup.py sdist
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
