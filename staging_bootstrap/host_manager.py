"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class HostManager(object):
    """Class to manage hosts"""

    hosts = {}

    @classmethod
    def add(cls, name, _host):
        cls.hosts[name] = _host

    @classmethod
    def get(cls, name):
        return cls.hosts[name]

# vi: ts=4 et:
