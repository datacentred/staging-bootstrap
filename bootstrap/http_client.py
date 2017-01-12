import httplib
import json

class HttpClient(object):
    """Class for interacting with hypervisors"""

    def __init__(self, host, port=8420):
        self.host = host
        self.port = port

    def get(self, uri):
        """Get data from the API"""
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request('GET', uri)
        resp = conn.getresponse()
        body = resp.read()
        if len(body):
            body = json.loads(body)
        else:
            body = None
        conn.close()
        return resp.status, body

    def post(self, uri, data):
        """Post data to the API"""
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request('POST', uri, json.dumps(data))
        resp = conn.getresponse()
        conn.close()
        return resp.status

    def put(self, uri, body=None):
        """Put data to the API"""
        conn = httplib.HTTPConnection(self.host, self.port)
        if body:
            body = json.dumps(data)
        conn.request('PUT', uri, body)
        resp = conn.getresponse()
        conn.close()
        return resp.status

    def delete(self, uri):
        """Delete a resource from the API"""
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request('DELETE', uri)
        resp = conn.getresponse()
        conn.close()
        return resp.status

# vi: ts=4 et:
