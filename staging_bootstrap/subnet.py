"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import ipaddress


class Subnet(object):
    """Container for a sub network"""

    def __init__(self, values):
        self._cidr = values['cidr']
        self._vlan = values['vlan']
        if 'gateway' in values:
            self._gateway = values['gateway']
        if 'nameservers' in values:
            self._nameservers = values['nameservers']

    @property
    def prefix(self):
        """Return the network prefix in dotted decimal notation"""
        return ipaddress.IPv4Network(unicode(self._cidr)).network_address

    @property
    def netmask(self):
        """Return the netmask in dotted decimal notation"""
        return ipaddress.IPv4Network(unicode(self._cidr)).netmask

    @property
    def vlan(self):
        """Return the VLAN tag"""
        return self._vlan

    @property
    def gateway(self):
        """Return the gateway if specified in dotted decimal notation"""
        if hasattr(self, '_gateway'):
            return self._gateway
        return None

    @property
    def nameservers(self):
        """Return an array of nameservers if specified in dotted decimal notation"""
        if hasattr(self, '_nameservers'):
            return self._nameservers
        return None


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
