"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

#import ConfigParser

from pkg_resources import resource_filename

from staging_bootstrap import dns as bs_dns
from staging_bootstrap import host as bs_host
from staging_bootstrap.configure import Configure as configure

# Disable long line warnings
# pylint: disable=C0301

# Default configuration
PUPPET_CONF = {
    'agent': {
        'server': 'puppet.example.com',
    },
}

PUPPET_CONF_SERVER_WITH_PUPPETDB = {
    'agent': {
        'server': 'puppet.example.com',
    },
    'master': {
        'storeconfigs': 'true',
        'storeconfigs_backend': 'puppetdb',
    },
}

# Gateway configuration, specifies DNS Alternate Names for X.509 generation
PUPPET_CONF_GATEWAY = {
    'main' : {
        'dns_alt_names': '*.example.com,*.staging.datacentred.services',
    },
    'agent': {
        'server': 'puppetca.example.com',
    },
}


def main():
    """Where the magic happens"""

    # Disable too many statements warning
    # pylint: disable=R0915

    configure.configure('config.yaml')
    config = configure.config()

    default_facts = {
        # This causes SSH to continue allowing root logins
        'staging_bootstrap': 'true',
    }

    default_excludes = [
        # Icinga2 requires storeconfigs which we don't have yet
        '::dc_profile::mon::icinga2',
    ]

    # Create the primary nameserver
    #
    # Establishes domain authority (e.g. ::domain and ::fqdn work)
    # Allows creation of DNS A and PTR records for hosts
    ns0 = bs_host.Host('ns0.example.com', {
        'role': 'dns_master',
         'networks': [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.250',
                'nameservers': [
                    '8.8.8.8',
                ]
            },
        ],
    })
    if not ns0.exists():
        ns0.create()
        ns0.install_puppet()
        ns0.configure_puppet(PUPPET_CONF)
        # Install prerequisite modules
        ns0.install_puppet_modules('theforeman-dns')
        # Apply the manifest
        ns0.puppet_apply(resource_filename('staging_bootstrap', 'data/manifests/dns_master/manifest.pp'))

    # Create the DNS helper
    dns = bs_dns.DNS(ns0)

    # Create the puppet CA
    #
    # Allows creation of SSL certificates, in particular the load-balancer so
    # that we can start refering to puppet.staging.datacentred.services generically
    # on all nodes
    puppetca = bs_host.Host('puppetca.example.com', {
        'role': 'puppet_ca',
        'memory': 4096,
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.3',
            },
        ],
    })
    dns.default(puppetca)
    if not puppetca.exists():
        puppetca.create()
        puppetca.install_puppet()
        puppetca.configure_puppet(PUPPET_CONF)
        # Install prerequisite modules
        puppetca.install_puppet_modules('puppetlabs-stdlib')
        # Install manifest prerequisites
        puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/hiera.yaml'), '/tmp/hiera.yaml')
        puppetca.scp(config.eyaml.public_key, '/tmp/public_key.pkcs7.pem')
        puppetca.scp(config.eyaml.private_key, '/tmp/private_key.pkcs7.pem')
        # Apply the manifest
        facts = {
            'deploy_user': config.github.username,
            'deploy_pass': config.github.password,
        }
        puppetca.puppet_apply(resource_filename('staging_bootstrap', 'data/manifests/puppet_ca/stage1/manifest.pp'), facts=facts)

    # Create a gateway
    #
    # All services from both example.com and cloud.example.com are accessed via this
    # load-balancer.  Once up we can begin using the Puppet CA server to provision
    # with production code
    gateway0 = bs_host.Host('gateway0.example.com', {
        'role': 'gateway',
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.5',
            },
            {
                'interface': 'ens4',
                'subnet': 'core-internet',
                'address': '185.43.217.139',
                'options': [
                    'post-up ip route replace default via 185.43.217.137',
                    'post-up ip route add 10.0.0.0/8 via 10.25.192.1',
                    'pre-down ip route del 10.0.0.0/8 via 10.25.192.1',
                    'pre-down ip route replace default via 10.25.192.1',
                ],
            },
        ],
    })
    dns.default(gateway0)
    if not gateway0.exists():
        gateway0.create()
        gateway0.install_puppet()
        gateway0.configure_puppet(PUPPET_CONF_GATEWAY)
        # Configure (hack) public networking
        gateway0.scp(resource_filename('staging_bootstrap', 'data/files/gateway/interfaces'), '/tmp/interfaces')
        gateway0.ssh('cat /tmp/interfaces >> /etc/network/interfaces')
        gateway0.ssh('ifup ens4')
        # Generate the certificates
        gateway0.ssh('/opt/puppetlabs/bin/puppet agent --test --tags non_existant', acceptable_exitcodes=[1])
        puppetca.ssh('/opt/puppetlabs/bin/puppet cert --allow-dns-alt-names sign gateway0.example.com')
        gateway0.puppet_agent('gateway', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        gateway0.puppet_disable()

    # Swing puppet behind the load-balancer
    dns.A('puppet.example.com', '10.25.192.2')
    puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/auth.conf'), '/tmp/auth.conf')
    puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/puppetserver.conf'), '/tmp/puppetserver.conf')
    puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/webserver.conf'), '/tmp/webserver.conf')
    puppetca.puppet_apply(resource_filename('staging_bootstrap', 'data/manifests/puppet_ca/stage2/manifest.pp'))

    # Create the postgres master
    #
    # Backend database used by puppetdb and foreman
    #
    # NOTE: Needs at least 4GB RAM for PGSQL to provision without modification
    postgres0 = bs_host.Host('postgres0.example.com', {
        'role': 'postgresql_master',
        'memory': 8192,
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.7',
            },
        ],
    })
    dns.default(postgres0)
    if not postgres0.exists():
        postgres0.create()
        postgres0.install_puppet()
        postgres0.configure_puppet(PUPPET_CONF)
        postgres0.puppet_agent('postgresql_master', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        postgres0.puppet_disable()

    # Create the postgres slave
    #
    # Functionally not required yet as it's a hot standby, but it's probably
    # easier to have the databases synchronized from the outset
    postgres1 = bs_host.Host('postgres1.example.com', {
        'role': 'postgresql_slave',
        'memory': 8192,
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.8',
            },
        ],
    })
    dns.default(postgres1)
    if not postgres1.exists():
        postgres1.create()
        postgres1.install_puppet()
        postgres1.configure_puppet(PUPPET_CONF)
        postgres1.puppet_agent('postgresql_slave', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        postgres1.puppet_disable()

    # Create puppetdb
    #
    # Allows code reliant on storeconfigs to work, for example service discovery
    # for monitoring will now work
    puppetdb0 = bs_host.Host('puppetdb0.example.com', {
        'role': 'puppetdb',
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.9',
            },
        ],
    })
    dns.default(puppetdb0)
    if not puppetdb0.exists():
        puppetdb0.create()
        puppetdb0.install_puppet()
        puppetdb0.configure_puppet(PUPPET_CONF)
        puppetdb0.puppet_agent('puppetdb', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        puppetdb0.puppet_disable()

 #   # Imbue puppet with store configs
 #   dns.A('puppetdb.example.com', u'10.25.192.2')
 #   puppetca.ssh('apt-get -y install puppetdb-termini')
 #   puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/routes.yaml'), '/etc/puppetlabs/puppet/routes.yaml')
 #   puppetca.scp(resource_filename('staging_bootstrap', 'data/files/puppet_ca/puppetdb.conf'), '/etc/puppetlabs/puppet/puppetdb.conf')
 #   puppetca.configure_puppet(PUPPET_CONF_SERVER_WITH_PUPPETDB)
 #   puppetca.ssh('systemctl restart puppetserver')

    # Create foreman
    foreman0 = bs_host.Host('foreman0.example.com', {
        'role': 'foreman',
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.10',
            },
        ],
    })
    dns.default(foreman0)
    if not foreman0.exists():
        foreman0.create()
        foreman0.install_puppet()
        foreman0.configure_puppet(PUPPET_CONF)
        foreman0.puppet_agent('foreman', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        foreman0.puppet_disable()
        # Foreman generates a random password which locks everyone out, so get this back under control
        foreman0.ssh('foreman-rake permissions:reset password=password')

    # Create the secondary nameserver
    ns1 = bs_host.Host('ns1.example.com', {
        'role': 'dns_slave',
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.251',
            },
        ],
    })
    dns.default(ns1)
    if not ns1.exists():
        ns1.create()
        ns1.install_puppet()
        ns1.configure_puppet(PUPPET_CONF)
        ns1.puppet_agent('dns_slave', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        ns1.puppet_disable()

    # Bootstrap the primary nameserver fully
    ns0.puppet_agent('dns_master', facts=default_facts, excludes=default_excludes)
    ns0.puppet_disable()

    # Create a puppet master
    #
    # This is required for the synchronization agents on the master to work
    # e.g. lsyncd will not work unless the target is defined.  This will also
    # enable storeconfigs and foreman reports
    puppet0 = bs_host.Host('puppet0.example.com', {
        'role': 'puppet_master',
        'networks':  [
            {
                'interface': 'ens3',
                'subnet': 'core-platform-services',
                'address': '10.25.192.4',
            },
        ],
    })
    dns.default(puppet0)
    if not puppet0.exists():
        puppet0.create()
        puppet0.install_puppet()
        puppet0.configure_puppet(PUPPET_CONF)
        puppet0.puppet_agent('puppet_master', facts=default_facts, excludes=default_excludes)
        # Prevent puppet runs until foreman is initialised with role data
        puppet0.puppet_disable()

    # Bootstrap the puppet ca fully
    puppetca.puppet_agent('puppet_ca', facts=default_facts, excludes=default_excludes)
    # Prevent puppet runs until foreman is initialised with role data
    puppetca.puppet_disable()


# vi: ts=4 et:
