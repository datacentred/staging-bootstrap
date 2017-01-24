"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

from pkg_resources import resource_filename

from staging_bootstrap import configure, host, nameserver
from staging_bootstrap.host import Host


# Disable long line warnings
# pylint: disable=C0301

def static(path):
    """Return the absolute path to a static file"""
    return resource_filename('staging_bootstrap', path)


def main():
    """Where the magic happens"""

    # Disable too many statements warning
    # pylint: disable=R0915

    config = configure('config.yaml')

    # Create the primary nameserver
    #
    # Establishes domain authority (e.g. ::domain and ::fqdn work)
    # Allows creation of DNS A and PTR records for hosts
    host('ns0.example.com').install_puppet_modules('theforeman-dns')
    host('ns0.example.com').puppet_apply(static('data/manifests/dns_master/manifest.pp'))

    # The CA needs access to these in order to checkout the puppet repo
    Host.facts = {
        'deploy_user': config.github.username,
        'deploy_pass': config.github.password,
    }

    # Create the puppet CA
    host('puppetca.example.com').install_puppet_modules('puppetlabs-stdlib')
    host('puppetca.example.com').scp(static('data/files/puppet_ca/hiera.yaml'), '/tmp/hiera.yaml')
    host('puppetca.example.com').scp(config.eyaml.public_key, '/tmp/public_key.pkcs7.pem')
    host('puppetca.example.com').scp(config.eyaml.private_key, '/tmp/private_key.pkcs7.pem')
    host('puppetca.example.com').puppet_apply(static('data/manifests/puppet_ca/stage1/manifest.pp'))

    # This fact allows root ssh logins
    Host.facts = {
        'staging_bootstrap': 'true',
    }

    # Don't run code reliant on the ENC or storeconfigs
    Host.excludes = [
        '::dc_profile::mon::icinga2',
    ]

    # Create a gateway
    host('gateway0.example.com').ssh('/opt/puppetlabs/bin/puppet agent --test --tags non_existant', acceptable_exitcodes=[1])
    host('puppetca.example.com').ssh('/opt/puppetlabs/bin/puppet cert --allow-dns-alt-names sign gateway0.example.com')
    host('gateway0.example.com').puppet_agent()

    # Swing puppet behind the load-balancer
    nameserver('example.com').a('puppet.example.com', '10.25.192.2')
    host('puppetca.example.com').scp(static('data/files/puppet_ca/auth.conf'), '/tmp/auth.conf')
    host('puppetca.example.com').scp(static('data/files/puppet_ca/puppetserver.conf'), '/tmp/puppetserver.conf')
    host('puppetca.example.com').scp(static('data/files/puppet_ca/webserver.conf'), '/tmp/webserver.conf')
    host('puppetca.example.com').puppet_apply(static('data/manifests/puppet_ca/stage2/manifest.pp'))

    # Create the postgres master
    host('postgres0.example.com').puppet_agent()

    # Create the postgres slave
    host('postgres1.example.com').puppet_agent()

    # Create puppetdb
    nameserver('example.com').a('puppetdb.example.com', '10.25.192.2')
    host('puppetdb0.example.com').puppet_agent()

    # Create foreman
    host('foreman0.example.com').puppet_agent()
    host('foreman0.example.com').ssh('foreman-rake permissions:reset password=password')

    # Bootstrap the primary nameserver fully
    host('ns0.example.com').puppet_agent()

    # Create the secondary nameserver
    host('ns1.example.com').puppet_agent()

    # Create a puppet master
    #
    # Inhibit port 8140 also so it doesn't start to try serving requests
    # Must happen before the CA comes up so lsyncd has a target to populate
    # Also remove the code directory which gets created for us
    host('puppet0.example.com').ssh('apt-get -y install iptables')
    host('puppet0.example.com').ssh('iptables -t filter -A INPUT -p tcp --dport 8140 -j DROP')
    host('puppet0.example.com').puppet_agent()
    host('puppet0.example.com').ssh('rm -rf /etc/puppetlabs/code/*')
    host('puppet0.example.com').ssh('chown puppet:puppet /etc/puppetlabs/code')

    # Bootstrap the puppet ca fully
    host('puppetca.example.com').puppet_agent()

    # Both masters are setup to use puppetdb and foreman reports allow requests to puppet0
    host('puppet0.example.com').ssh('iptables -t filter -D INPUT -p tcp --dport 8140 -j DROP')


# vi: ts=4 et:
