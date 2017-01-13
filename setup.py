#!/usr/bin/python

"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import setuptools

setuptools.setup(
    name = 'staging_bootstrap',
    version = '0.0.1',
    packages = [
        'staging_bootstrap',
    ],
    entry_points = {
        'console_scripts': [
            'staging-create=staging_bootstrap.create:main',
            'staging-destroy=staging_bootstrap.destroy:main',
        ],
    },
)

# vi: ts=4 et:
