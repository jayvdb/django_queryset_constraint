#!/bin/bash

docker rm -f django_constraint_postgres
docker run --name django_constraint_postgres -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres
rm django_constraint_triggers/migrations/0*
until pg_isready -h localhost; do
  sleep 1
done
./manage.py makemigrations
./manage.py migrate
