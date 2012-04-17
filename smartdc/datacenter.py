import sys
import json

import requests
from http_signature.requests_auth import HTTPSignatureAuth

from .machine import Machine

API_HOST_SUFFIX = '.api.joyentcloud.com'
API_VERSION = '~6.5'

KNOWN_LOCATIONS = {
    u'us-east-1': u'https://us-east-1.api.joyentcloud.com',
    u'us-sw-1':   u'https://us-sw-1.api.joyentcloud.com',
    u'us-west-1': u'https://us-west-1.api.joyentcloud.com',
    u'eu-ams-1':  u'https://eu-ams-1.api.joyentcloud.com',
}

DEFAULT_LOCATION = 'us-west-1'

DEFAULT_HEADERS = {
    'Accept':        'application/json',
    'Content-Type':  'application/json; charset=UTF-8',
    'X-Api-Version': API_VERSION
}

DEBUG_CONFIG = {'verbose': sys.stderr}

class DataCenter(object):
    def __init__(self, location=None, key_id=None, secret=None, 
                headers=None, login=None, config=None, known_locations=None):
        self.location = location or DEFAULT_LOCATION
        self.known_locations = known_locations or KNOWN_LOCATIONS
        if self.location in self.known_locations:
            self.base_url = self.known_locations[self.location]
        elif '.' in self.location or self.location == 'localhost':
            self.base_url = 'https://' + self.location
        else:
            self.base_url = 'https://' + self.location + API_HOST_SUFFIX
        self.config = config or {}
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
    
    def __str__(self):
        if self.login != 'my':
            user_string = self.login + '@'
        else:
            user_string = ''
        return '<{cls}: {user_string}{location}>'.format(cls=self.__class__.__name__,
            user_string=user_string, location=self.location)
    
    def __repr__(self):
        if self.login != 'my':
            user_string = '<{0}> '.format(self.login)
        else:
            user_string = ''
        return '<{module}.{cls}: {name}at <{loc}>>'.format(module=self.__module__,
            cls=self.__class__.__name__, name=user_string, loc=self.location)
        
    @property
    def url(self):
        return '{base_url}/{login}/'.format(base_url=self.base_url, login=self.login)
    
    def authenticate(self, key_id=None, secret=None):
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret)
    
    def request(self, method, path, headers=None, **kwargs):
        full_path = self.url + path
        request_headers = {}
        request_headers.update(self.default_headers)
        if headers:
            request_headers.update(headers)
        resp = requests.request(method, full_path, auth=self.auth, 
            headers=request_headers, config=self.config, **kwargs)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            if resp.headers['content-type'] == 'application/json':
                return (json.loads(resp.content), resp)
            else:
                return (resp.content, resp)
        else:
            return (None, resp)
    
    def api(self):
        resp = requests.request('GET', self.base_url)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            return json.loads(resp.content)
    
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
    
    def me(self):
        j, _ = self.request('GET', '')
        if 'login' in j and self.login == 'my':
            self.login = j['login']
        return j
    
    def datacenters(self):
        j, _ = self.request('GET', 'datacenters')
        self.known_locations.update(j)
        return j
    
    def datacenter(self, name):
        # The base form of this, as below, simply sets up a redirect. 
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
    
    def num_machines(self):
        _, r = self.request('HEAD', 'machines')
        num = r.headers.get('x-resource-count', 0)
        return int(num)
    
    def raw_machine_data(self, machine_id):
        if isinstance(machine_id, dict):
            machine_id = machine_id['id']
        j, _ = self.request('GET', 'machines/' + str(machine_id))
        return j
    
    def machines(self, machine_type=None, name=None, dataset=None, state=None, 
            memory=None, tombstone=None, tag_dict=None, credentials=False, 
            paged=False, limit=None, offset=None):
        params = {}
        if machine_type:
            params['type'] = machine_type
        if name:
            params['name'] = name
        if dataset:
            if isinstance(dataset, dict):
                dataset = dataset['id']
            params['dataset'] = dataset
        if state:
            params['state'] = state
        if memory:
            params['memory'] = memory
        if tombstone:
            params['tombstone'] = tombstone
        if tag_dict:
            for k, v in tag_dict.items():
                params['tag.' + str(k)] = v
        if credentials:
            params['credentials'] = True
        if limit:
            params['limit'] = limit
        else:
            limit = 1000
        if offset:
            params['offset'] = offset
        else:
            offset = 0
        machines = []
        while True:
            j, r = self.request('GET', 'machines', params=params)
            machines.extend(j)
            if not paged:
                query_limit = int(r.headers['x-query-limit'])
                resource_count = int(r.headers['x-resource-count'])
                if resource_count > query_limit:
                    data['offset'] = params.get('offset', offset) + params.get('limit', limit)
                else:
                    break
            else:
                break
        return [Machine(data=m, datacenter=self) for m in machines]
    
    def create_machine(self, name=None, package=None, dataset=None,
            metadata_dict=None, tag_dict=None):
        params = {}
        if name:
            params['name'] = name
        if package:
            if isinstance(package, dict):
                package = package['name']
            params['package'] = package
        if dataset:
            if isinstance(dataset, dict):
                dataset = dataset['id']
            params['dataset'] = dataset
        if metadata_dict:
            for k, v in metadata_dict.items():
                params['metadata.' + str(k)] = v
        if tag_dict:
            for k, v in tag_dict.items():
                params['tag.' + str(k)] = v
        j, r = self.request('POST', 'machines', params=params)
        return Machine(j, self)
    

