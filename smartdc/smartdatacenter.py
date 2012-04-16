import json

import requests
from http_signature.requests_auth import HTTPSignatureAuth

API_HOST_SUFFIX = '.api.joyentcloud.com'
API_VERSION = '~6.5'

LOCATIONS = ['us-east-1', 'us-west-1', 'us-sw-1', 'eu-ams-1']
DEFAULT_LOCATION = LOCATIONS[1]

DEFAULT_HEADERS = {'Accept': 'application/json',
'Content-Type': 'application/json; charset=UTF-8',
'X-Api-Version': API_VERSION}

REQUEST_URL = 'https://{location}{host_suffix}/{login}/{resource}'

class DataCenterConnection(object):
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
        request_headers = {}
        request_headers.update(self.default_headers)
        if headers:
            request_headers.update(headers)
        resp = requests.request(method, full_path, auth=self.auth, headers=request_headers, **kwargs)
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
        j, _ = self.request('GET', 'keys/' + key_id)
        return j
    
    def add_key(self, key_id, key):
        data = json.dumps({'name': key_id, 'key': key})
        j, _ = self.request('POST', 'keys', data=data)
        return j
    
    def delete_key(self, key_id):
        j, r = self.request('DELETE', 'keys/' + key_id)
        r.raise_for_status()
        return j
    
