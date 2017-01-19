"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import yaml

from staging_bootstrap import dotdict
from staging_bootstrap import host
from staging_bootstrap import subnet

class Configure(object):
    """Manages global configuration"""

    @classmethod
    def configure(cls, path):
        """Parse the static configuration file and set up global data structures"""

        with open(path, 'r') as conf_file:
            data = yaml.load(conf_file.read())

        for k, v in data['subnets'].items():
            subnet.SubnetManager.add(k, subnet.Subnet(v))

        for k, v in data['hosts'].items():
            if k == 'defaults':
                host.Host.defaults = v
            else:
                host.HostManager.add(k, host.Host(k, v))

        return dotdict.DotDict(data['config'])

# vi: ts=4 et:
