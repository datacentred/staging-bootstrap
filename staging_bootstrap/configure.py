"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import yaml

from staging_bootstrap import dotdict

class Configure(object):
    """Manages global configuration"""

    @classmethod
    def configure(cls, path):
        """Parse the static configuration file and set up global data structures"""

        with open(path, 'r') as conf_file:
            data = yaml.load(conf_file.read())

        cls._config = dotdict.DotDict(data['config'])

    @classmethod
    def config(cls):
        """Return the configuration dictionary"""
        return cls._config

# vi: ts=4 et:
