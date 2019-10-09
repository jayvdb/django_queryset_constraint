#!/bin/bash

rm -f django_queryset_constraint/migrations/0*
rm -rf build/ dist/ django_queryset_constraint.egg-inf
python3 setup.py sdist
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
