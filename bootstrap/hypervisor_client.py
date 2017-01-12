import http_client

class HypervisorClient(http_client.HttpClient):
    """Class for interacting with hypervisors"""

    def __init__(self, host, port=8420):
        super(HypervisorClient, self).__init__(host, port)

    def network_list(self):
        """Return a list of all networks"""
        code, body = self.get('/networks')
        if code != 200:
            raise RuntimeError
        return body

    def network_create(self, name, bridge, tag):
        """Create a network if it doesn't exist"""
        uri = '/networks/{}'.format(name)
        code, _ = self.get(uri)
        if code == 404:
            body = {'bridge': bridge, 'vlan': tag}
            if self.post(uri, body) != 201:
                raise RuntimeError

    def network_delete(self, name):
        """Delete a network if it exists"""
        uri = '/networks/{}'.format(name)
        code, _ = self.get(uri)
        if code == 200:
            if self.delete(uri) != 204:
                raise RuntimeError

    def host_list(self):
        """Return a list of all hosts"""
        code, body = self.get('/hosts')
        if code != 200:
            raise RuntimeError
        return body

    def host_create(self, name, memory, disks, networks, location, cmdline):
        """Create a host if not already defined"""
        uri = '/hosts/{}'.format(name)
        code, _ = self.get(uri)
        if code == 404:
            body = {
                'memory': memory,
                'disks': disks,
                'networks': networks,
                'install': True,
                'location': location,
                'cmdline': cmdline
            }
            if self.post(uri, body) != 201:
                raise RuntimeError

    def host_delete(self, name):
        """Delete a host from the hypervisor"""
        uri = '/hosts/{}'.format(name)
        code, _ = self.get(uri)
        if code == 200:
            if self.delete(uri) != 204:
                raise RuntimeError

    def host_get(self, name):
        """Get information about a host"""
        uri = '/hosts/{}'.format(name)
        code, body = self.get(uri)
        if code != 200:
            raise RuntimeError
        return body

    def host_start(self, name):
        """Start a host"""
        uri = '/hosts/{}/start'.format(name)
        if self.put(uri) != 204:
            raise RuntimeError

# vi: ts=4 et:
