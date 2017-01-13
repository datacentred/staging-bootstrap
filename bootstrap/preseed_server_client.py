"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

from bootstrap import http_client


class PreseedServerClient(http_client.HttpClient):
    """Class for interacting with the preseed server"""

    def __init__(self, host, port=8421):
        super(PreseedServerClient, self).__init__(host, port)


    def host_create(self, name, preseed, finish, metadata=None):
        """Create a host entry"""
        uri = '/hosts/{}'.format(name)
        code, _ = self.get(uri)
        if code == 404:
            body = {'preseed': preseed, 'finish': finish}
            if metadata:
                body['metadata'] = metadata
            if self.post(uri, body) != 201:
                raise RuntimeError


    def host_delete(self, name):
        """Delete a host entry"""
        uri = '/hosts/{}'.format(name)
        code, _ = self.get(uri)
        if code == 200:
            if self.delete(uri) != 204:
                raise RuntimeError


# vi: ts=4 et:
