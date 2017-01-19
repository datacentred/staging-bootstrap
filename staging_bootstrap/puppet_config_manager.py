"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class PuppetConfigManager(object):
    """Manages puppet configurations"""

    configs = {}

    @classmethod
    def add(cls, name, config):
        """Adds a configuration file to the collection"""
        cls.configs[name] = config

    @classmethod
    def get(cls, name):
        """Retrieves a configuration file from the collection"""
        try:
            return cls.configs[name]
        except KeyError:
            return None

# vi: ts=4 et:

