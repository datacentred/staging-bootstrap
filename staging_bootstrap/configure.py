"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import yaml

from staging_bootstrap.dotdict import DotDict
from staging_bootstrap.host import Host
from staging_bootstrap.host_manager import HostManager
from staging_bootstrap.nameserver import NameserverManager, Nameserver
from staging_bootstrap.subnet import SubnetManager, Subnet
from staging_bootstrap.puppet import PuppetConfigManager, PuppetConfig

class Configure(object):
    """Manages global configuration"""

    @classmethod
    def configure(cls, path):
        """Parse the static configuration file and set up global data structures"""

        with open(path, 'r') as conf_file:
            data = yaml.load(conf_file.read())

        for k, v in data['puppet'].items():
            if k == 'config':
                for name, config in v.items():
                    PuppetConfigManager.add(name, PuppetConfig(config))

        for k, v in data['subnets'].items():
            SubnetManager.add(k, Subnet(v))

        for k, v in data['hosts'].items():
            if k == 'defaults':
                Host.defaults = v
            else:
                HostManager.add(k, Host(k, v))

        for k, v in data['dns'].items():
            NameserverManager.add(k, Nameserver(v))

        return DotDict(data['config'])

# vi: ts=4 et:
