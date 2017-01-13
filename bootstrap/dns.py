"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import subprocess


class DNS(object):
    """Wrapper for DDNS functionality"""

    # Disable invalid name warnings
    # pylint: disable=C0103

    def __init__(self, host):
        self.host = host


    def A(self, fqdn, ip):
        """Add an A record"""

        if ip not in subprocess.check_output(['dig', '@' + self.host.primary_address(), '+short', fqdn, 'A']):
            self.host.ssh('echo -e "server 127.0.0.1\nupdate add {} 604800 A {}\nsend" | nsupdate -k /etc/bind/rndc.key'.format(fqdn, ip))


    def PTR(self, fqdn, ip):
        """Add a PTR record"""

        arpa = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
        if fqdn not in subprocess.check_output(['dig', '@' + self.host.primary_address(), '+short', arpa, 'PTR']):
            self.host.ssh('echo -e "server 127.0.0.1\nupdate add {} 604800 PTR {}\nsend" | nsupdate -k /etc/bind/rndc.key'.format(arpa, fqdn))


    def default(self, host):
        """Add default A and PTR records for a host"""

        self.A(host.name, host.primary_address())
        self.PTR(host.name, host.primary_address())
