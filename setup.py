import os
import sys

from setuptools import find_packages, setup

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 6)

# This check and everything above must remain compatible with Python 2.7.
if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write(
        """
==========================
Unsupported Python version
==========================

This version of django_queryset_constraint requires Python {}.{}, but you are
trying to install it on Python {}.{}.

This may be because you are using a version of pip that doesn't
understand the python_requires classifier. Make sure you
have pip >= 9.0 and setuptools >= 24.2, then try again:
    $ python -m pip install --upgrade pip setuptools
    $ python -m pip install django_queryset_constraint
This will install the latest version of django_queryset_constraint which works on
your version of Python.""".format(
            *(REQUIRED_PYTHON + CURRENT_PYTHON)
        )
    )
    sys.exit(1)


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name="django_queryset_constraint",
    version="1.0.4",
    python_requires=">={}.{}".format(*REQUIRED_PYTHON),
    url="https://github.com/magenta-aps/django_queryset_constraint",
    author="Emil Madsen",
    author_email="emil@magenta.dk",
    description=("A library for writing reliable data invariants in Django."),
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    license="MPL-2.0",
    packages=find_packages(),
    include_package_data=True,
    download_url="https://github.com/magenta-aps/django_queryset_constraint/archive/master.zip",
    zip_safe=False,
    install_requires=["Django"],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=["django"],
    project_urls={
        "Source": "https://github.com/magenta-aps/django_queryset_constraint",
        # TODO: Add documentation URL
    },
)
