"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import struct

import ipaddress


class Subnet(object):
    """Container for a sub network"""

    def __init__(self, subnet, gateway, nameserver, vlan):
        """Initialise a subnet"""
        self.subnet = ipaddress.IPv4Network(subnet)
        self.gateway = ipaddress.IPv4Address(gateway)
        self.nameserver = ipaddress.IPv4Address(nameserver)
        self.vlan = vlan
        self.allocations = [self.gateway]


    def get_netmask(self):
        """Return the subnet mask"""
        return self.subnet.netmask


    def get_gateway(self):
        """Return the default gateway"""
        return self.gateway.exploded


    def set_nameserver(self, nameserver):
        """Set the nameserver"""
        self.nameserver = ipaddress.IPv4Address(nameserver)


    def get_nameserver(self):
        """Get the nameserver"""
        return self.nameserver.exploded


    def get_vlan(self):
        """Get the VLAN for the subnet"""
        return self.vlan


    def allocate_address(self, fixed=False):
        """Try allocate a fixed address, or dynamic if not defined"""
        if fixed:
            address = ipaddress.IPv4Address(fixed)
            if address not in self.subnet:
                raise ValueError('address not in subnet')
            if address in self.allocations:
                raise ValueError('address allocation already exists')
        else:
            # Get the network prefix and convert to an integer
            iaddress = struct.unpack('>I', self.subnet.network_address.packed)[0]
            # Increment through the subnet and look for a spare address
            # Note: num_addresses is 255 for a /24, by incrementing by 1 if no
            # allocations are found then address is the boradcast address and
            # we can trap the error condition
            for _ in range(1, self.subnet.num_addresses + 1):
                iaddress = iaddress + 1
                address = ipaddress.IPv4Address(struct.pack('>I', iaddress))
                if address not in self.allocations:
                    break
            if address == self.subnet.broadcast_address:
                raise OverflowError('no free addresses')
        self.allocations.append(address)
        return address.exploded


# vi: ts=4 et:
