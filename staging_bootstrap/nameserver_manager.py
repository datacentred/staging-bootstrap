"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class NameserverManager(object):

    nameservers = {}

    @classmethod
    def add(cls, name, nameserver):
        cls.nameservers[name] = nameserver

    @classmethod
    def get(cls, name):
        return cls.nameservers[name]


# vi: ts=4 et:
