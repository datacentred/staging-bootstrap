"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class SubnetManager(object):
    """Class to manage defined subnets"""

    subnets = {}

    @classmethod
    def add(cls, name, subnet):
        cls.subnets[name] = subnet

    @classmethod
    def get(cls, name):
        return cls.subnets[name]


# vi: ts=4 et:
