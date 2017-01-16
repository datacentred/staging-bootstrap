#!/usr/bin/python

"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import os
import setuptools

def package_data(path):
    paths = []
    for path, directories, files in os.walk(path):
        for filename in files:
            paths.append(os.path.join('..', path, filename))
    return paths

setuptools.setup(
    name = 'staging_bootstrap',
    version = '0.0.1',
    packages = [
        'staging_bootstrap',
    ],
    package_data = {
        'staging_bootstrap': package_data('staging_bootstrap/data'),
    },
    entry_points = {
        'console_scripts': [
            'staging-create=staging_bootstrap.create:main',
            'staging-destroy=staging_bootstrap.destroy:main',
        ],
    },
)

# vi: ts=4 et:
