"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import dns.resolver
import dns.reversename

from staging_bootstrap.formatter import info
from staging_bootstrap.host_manager import HostManager

class Nameserver(object):
    """Wrapper for DDNS functionality"""

    # Disable invalid name warnings
    # pylint: disable=C0103

    def __init__(self, values):
        self.host = values['host']
        self.subnets = values['subnets']

    def a(self, fqdn, ip):
        """Add an A record"""
        host = HostManager.get(self.host)
        if host.exists():
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [host.address]
                resolver.query(fqdn, 'A')
            except dns.resolver.NXDOMAIN:
                info('Creating A record for {}: {}'.format(fqdn, ip))
                host.ssh('echo -e "server 127.0.0.1\nupdate add {} 604800 A {}\nsend" | nsupdate -k /etc/bind/rndc.key'.format(fqdn, ip))

    def ptr(self, fqdn, ip):
        """Add a PTR record"""
        host = HostManager.get(self.host)
        if host.exists():
            arpa = dns.reversename.from_address(ip).to_text()
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [host.address]
                resolver.query(arpa, 'PTR')
            except dns.resolver.NXDOMAIN:
                info('Creating PTR record for {}: {}'.format(ip, arpa))
                host.ssh('echo -e "server 127.0.0.1\nupdate add {} 604800 PTR {}\nsend" | nsupdate -k /etc/bind/rndc.key'.format(arpa, fqdn))


class NameserverManager(object):

    nameservers = {}

    @classmethod
    def add(cls, name, nameserver):
        cls.nameservers[name] = nameserver

    @classmethod
    def get(cls, name):
        return cls.nameservers[name]


def nameserver(domain):
    return NameserverManager.get(domain)


# vi: ts=4 et:
