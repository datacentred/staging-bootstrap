"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

from staging_bootstrap.configure import Configure
from staging_bootstrap.host_manager import HostManager
from staging_bootstrap.nameserver_manager import NameserverManager

def configure(path):
    """Configures the system"""
    return Configure.configure(path)


def host(name):
    """DSL to get and possibly provison a host"""

    # Lazily provision the first time we reference a host
    _host = HostManager.get(name)
    if not _host.exists():
        # Add A and PTR records so that `hostname -f` works as expected
        dns = NameserverManager.get(_host.domain)
        dns.a(_host.name, _host.address)
        dns.ptr(_host.name, _host.address)
        # Create the host, installing and configuring puppet
        _host.create()
        _host.install_puppet()
        _host.configure_puppet()
    return _host


def nameserver(domain):
    """DSL to get a nameserver for a domain"""
    return NameserverManager.get(domain)

# vi: ts=4 et:
