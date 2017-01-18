"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import yaml

from staging_bootstrap import dotdict
from staging_bootstrap import subnet

class Configure(object):
    """Manages global configuration"""

    @classmethod
    def configure(cls, path):
        """Parse the static configuration file and set up global data structures"""

        with open(path, 'r') as conf_file:
            data = yaml.load(conf_file.read())

        cls._config = dotdict.DotDict(data['config'])

        cls._subnets = {}
        for k, v in data['subnets'].items():
            cls._subnets[k] = subnet.Subnet(v)

    @classmethod
    def config(cls):
        """Return the configuration dictionary"""
        return cls._config

    @classmethod
    def subnets(cls):
        """Return the subnet dictionary"""
        return cls._subnets

# vi: ts=4 et:
