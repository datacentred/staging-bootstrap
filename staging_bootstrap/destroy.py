"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

from staging_bootstrap import hypervisor_client
from staging_bootstrap.formatter import info
from staging_bootstrap.formatter import detail


def main():
    """Destroy any resources accociated with guests"""

    hypervisor = hypervisor_client.HypervisorClient('localhost')

    info('Deleting hosts ...')
    hosts = hypervisor.host_list()
    for host in hosts:
        detail(host['name'])
        hypervisor.host_delete(host['name'])

    info('Deleting networks ...')
    networks = hypervisor.network_list()
    for network in networks:
        detail(network['name'])
        hypervisor.network_delete(network['name'])


# vi: ts=4 et:
