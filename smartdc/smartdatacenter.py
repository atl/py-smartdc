import sys
import json

import requests
from http_signature.requests_auth import HTTPSignatureAuth

API_HOST_SUFFIX = '.api.joyentcloud.com'
API_VERSION = '~6.5'

LOCATIONS = ['us-east-1', 'us-west-1', 'us-sw-1', 'eu-ams-1']
DEFAULT_LOCATION = LOCATIONS[1]

DEFAULT_HEADERS = {'Accept': 'application/json',
    'Content-Type': 'application/json; charset=UTF-8',
    'X-Api-Version': API_VERSION
}

class DataCenter(object):
    def __init__(self, location=None, key_id=None, secret=None, headers=None, login=None):
        self.location = location or DEFAULT_LOCATION
        self.host = self.location + API_HOST_SUFFIX
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret)
        else:
            self.auth = None
        self.default_headers = DEFAULT_HEADERS
        if headers:
            self.default_headers.update(headers)
        if login:
            self.login = login
        else:
            self.login = 'my'
        self.base_url = 'https://{location}{host_suffix}/{login}/'.format(
            location=self.location, host_suffix=API_HOST_SUFFIX, login=self.login)
    
    def authenticate(self, key_id=None, secret=None):
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret)
    
    def request(self, method, path, headers=None, **kwargs):
        full_path = self.base_url + path
        config = {'verbose': sys.stderr}
        request_headers = {}
        request_headers.update(self.default_headers)
        if headers:
            request_headers.update(headers)
        resp = requests.request(method, full_path, auth=self.auth, headers=request_headers, config=config, **kwargs)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            return (json.loads(resp.content), resp)
        else:
            return (None, resp)
    
    def keys(self):
        j, _ = self.request('GET', 'keys')
        return j
    
    def key(self, key_id):
        j, _ = self.request('GET', 'keys/' + str(key_id))
        return j
    
    def add_key(self, key_id, key):
        data = json.dumps({'name': str(key_id), 'key': str(key)})
        j, _ = self.request('POST', 'keys', data=data)
        return j
    
    def delete_key(self, key_id):
        j, r = self.request('DELETE', 'keys/' + str(key_id))
        r.raise_for_status()
        return j
    
    def datacenters(self):
        j, _ = self.request('GET', 'datacenters')
        return j
    
    def datacenter(self, name):
        # j, _ = self.request('GET', 'datacenters/' + str(name))
        dc = DataCenter(location=name, headers=self.default_headers, login=self.login)
        dc.auth = self.auth
        return dc
    
    def datasets(self):
        j, _ = self.request('GET', 'datasets')
        return j
    
    def dataset(self, dataset_id):
        if isinstance(dataset_id, dict):
            dataset_id = dataset_id['id']
        j, _ = self.request('GET', 'datasets/' + str(dataset_id))
        return j
    
    def packages(self):
        j, _ = self.request('GET', 'packages')
        return j
    
    def package(self, name):
        if isinstance(name, dict):
            name = name['name']
        j, _ = self.request('GET', 'packages/' + str(name))
        return j
    

