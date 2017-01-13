"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import socket
import subprocess
import sys

# 3rd party imports
import crypt
import paramiko

# Local imports
from staging_bootstrap import hypervisor_client
from staging_bootstrap import preseed_server_client
from staging_bootstrap.formatter import info
from staging_bootstrap.formatter import detail
from staging_bootstrap.util import wait_for


class Host(object):
    """Container for a host object"""

    # Class variable to hold install location
    location = ""

    def __init__(self, name, networks, **kwargs):
        """Initialise a host"""

        self.name = name
        self.networks = networks
        self.addresses = [subnet.allocate_address(address) for subnet, address in networks]
        self.ram = kwargs.get('ram', 512)
        self.disks = kwargs.get('disks', [8])
        self.password = 'password'


    def primary_address(self):
        """Returns the primary IP address"""

        return self.addresses[0]


    def primary_subnet(self):
        """Returns the primary subnet"""

        return self.networks[0][0]


    def exists(self):
        """Check if a host exists"""

        lines = subprocess.check_output(['virsh', 'list', '--all']).split("\n")[2:-2]
        for line in lines:
            if self.name in line:
                return True
        return False


    def create(self):
        """Create a host, blocking until it is provisioned and SSH is running"""

        info('Creating host {} ...'.format(self.name))
        detail('Memory  {} MB'.format(self.ram))
        detail('Disks   {} GB'.format(self.disks))
        detail('Address {}'.format(self.primary_address()))
        detail('Netmask {}'.format(self.primary_subnet().get_netmask()))
        detail('Gateway {}'.format(self.primary_subnet().get_gateway()))
        detail('DNS     {}'.format(self.primary_subnet().get_nameserver()))

        preseed = preseed_server_client.PreseedServerClient('localhost')
        hypervisor = hypervisor_client.HypervisorClient('localhost')

        # Create a preseed entry
        metadata = {
            'root_password': crypt.crypt(self.password, '$6$salt'),
            'finish_url': 'http://{}:8421/hosts/{}/finish'.format(self.primary_subnet().get_gateway(), self.name),
        }
        preseed.host_create(self.name, 'preseed.xenial.erb', 'finish.xenial.erb', metadata)

        # Create networks on the hypervisor
        info('Creating networks ...')
        network_names = []
        for subnet, _ in self.networks:
            name = 'vlan:{}'.format(subnet.get_vlan())
            network_names.append(name)
            hypervisor.network_create(name, 'br0', subnet.get_vlan())

        # Set the preseed kernel command line parameters, mostly static network options
        extra_args = [
            'auto=true',
            'priority=critical',
            'vga=normal',
            'hostname={}'.format(self.name),
            'domain=example.com',
            'url=http://{}:8421/hosts/{}/preseed'.format(self.primary_subnet().get_gateway(), self.name),
            'netcfg/choose_interface=auto',
            'netcfg/disable_autoconfig=true',
            'netcfg/get_ipaddress={}'.format(self.primary_address()),
            'netcfg/get_netmask={}'.format(self.primary_subnet().get_netmask()),
            'netcfg/get_gateway={}'.format(self.primary_subnet().get_gateway()),
            'netcfg/get_nameservers={}'.format(self.primary_subnet().get_nameserver()),
            'netcfg/confirm_static=true'
        ]

        # Create the host on the hypervisor
        # This is a non-blocking operation, so we need to poll for completion
        info('Creating host ...')
        hypervisor.host_create(self.name, self.ram, self.disks, network_names,
                               self.location, ' '.join(extra_args))
        delta = self.wait_for_state(hypervisor, 'shut off')
        detail('Host created in {}s'.format(delta))

        info('Rebooting host ...')
        hypervisor.host_start(self.name)

        # Wait for SSH to become available for provisioning
        info('Waiting for SSH ...')
        delta = self.wait_for_port(22)
        detail('Port listening in {}s'.format(delta))

        # Clean up to the preseed server
        preseed.host_delete(self.name)


    def wait_for_state(self, hypervisor, state):
        """Wait for a host to enter a specific state"""
        def cond():
            """Closure to poll host state"""
            return hypervisor.host_get(self.name)['state'] == state
        return wait_for(cond)


    def wait_for_port(self, port):
        """Wait for a port to start listening"""
        def cond():
            """Closure to socket state"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((self.primary_address(), port))
            except IOError:
                return False
            return True
        return wait_for(cond)


    def ssh(self, command, **kwargs):
        """SSH onto a host and execute a command"""

        if 'acceptable_exitcodes' in kwargs:
            acceptable_exitcodes = kwargs['acceptable_exitcodes']
        else:
            acceptable_exitcodes = [0]

        info('Executing on {}: {}'.format(self.name, command))
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.primary_address(), username='root', password=self.password)
        channel = client.get_transport().open_session()
        channel.set_combine_stderr(True)
        channel.exec_command(command)
        while True:
            if channel.recv_ready():
                sys.stdout.write(channel.recv(8192))
            if channel.exit_status_ready():
                break
        detail("Exited with status {}".format(channel.recv_exit_status()))
        if channel.recv_exit_status() not in acceptable_exitcodes:
            raise RuntimeError('command execution failed')


    def scp(self, source, target):
        """SCP a local file to a host"""

        info('Copying {} to {} on {}'.format(source, target, self.name))
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.primary_address(), username='root', password=self.password)
        sftp = client.open_sftp()
        sftp.put(source, target)


    def install_puppet(self):
        """Install puppet on the host"""

        deb = 'puppetlabs-release-pc1-xenial.deb'
        self.ssh(r'wget -O /tmp/{0} https://apt.puppet.com/{0}'.format(deb))
        self.ssh(r'dpkg -i --force-all /tmp/{0}'.format(deb))
        self.ssh(r'apt-get update')
        self.ssh(r'echo START=no > /etc/default/puppet')
        self.ssh(r'apt-get -y -o DPkg::Options::=--force-confold install puppet-agent')
        # Temporary hack for Icinga 2 (prevents restarts and box death!)
        self.ssh(r'mkdir -p /var/lib/puppet')
        self.ssh(r'ln -s /etc/puppetlabs/puppet/ssl /var/lib/puppet')


    def configure_puppet(self, config):
        """Configure puppet"""

        text = ''
        for section in config:
            text += "[{}]\n".format(section)
            for option in config[section]:
                text += "{} = {}\n".format(option, config[section][option])
        self.ssh('echo \'{}\' > /etc/puppetlabs/puppet/puppet.conf'.format(text))


    def install_puppet_modules(self, modules):
        """Install puppet modules"""

        if isinstance(modules, str):
            modules = modules.split()
        for module in modules:
            self.ssh(r'/opt/puppetlabs/bin/puppet module install {}'.format(module))


    def puppet_apply(self, manifest, **kwargs):
        """Transfer and apply a manifest"""

        target = '/tmp/manifest.pp'
        self.scp(manifest, target)
        command = ''
        if 'facts' in kwargs:
            command = ' '.join(('FACTER_' + x + '=' + kwargs['facts'][x] for x in kwargs['facts'])) + ' '
        command = command + '/opt/puppetlabs/bin/puppet apply ' + target
        self.ssh(command)


    def puppet_agent(self, role, **kwargs):
        """Run puppet against the master specifying role and excluded classes"""

        command = 'FACTER_role=' + role + ' '
        if 'facts' in kwargs:
            command = command + ' '.join(('FACTER_' + x + '=' + kwargs['facts'][x] for x in kwargs['facts'])) + ' '
        if 'excludes' in kwargs:
            command = command + 'FACTER_excludes=' + ','.join(kwargs['excludes']) + ' '
        command = command + '/opt/puppetlabs/bin/puppet agent --test'
        self.ssh(command, acceptable_exitcodes=[0, 2])


    def puppet_disable(self):
        """Disable automatic puppet runs"""

        self.ssh('/opt/puppetlabs/bin/puppet agent --disable')


# vi: ts=4 et:
