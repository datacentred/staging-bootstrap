#!/usr/bin/python

"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import setuptools

setuptools.setup(
    name = 'bootstrap',
    version = '0.0.1',
    packages = [
        'bootstrap',
    ],
    entry_points = {
        'console_scripts': [
            'staging-create=bootstrap.create:main',
            'staging-destroy=bootstrap.destroy:main',
        ],
    },
)

# vi: ts=4 et:
