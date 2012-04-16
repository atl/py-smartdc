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

DEFAULT_CONFIG = {'verbose': sys.stderr}

class DataCenter(object):
    def __init__(self, location=None, key_id=None, secret=None, 
                headers=None, login=None, config=None):
        self.location = location or DEFAULT_LOCATION
        self.host = self.location + API_HOST_SUFFIX
        self.config = config or DEFAULT_CONFIG
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
    
    @property
    def base_url(self):
        return 'https://{location}{host_suffix}/{login}/'.format(
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
        resp = requests.request(method, full_path, auth=self.auth, 
            headers=request_headers, config=self.config, **kwargs)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            return (json.loads(resp.content), resp)
        else:
            return (None, resp)
    
    def api(self):
        resp = requests.request('GET', 'https://{location}{host_suffix}/'.format(
                location=self.location, host_suffix=API_HOST_SUFFIX))
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
        return j
    
    def datacenters(self):
        j, _ = self.request('GET', 'datacenters')
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
        data = {}
        if machine_type:
            data['type'] = machine_type
        if name:
            data['name'] = name
        if dataset:
            data['dataset'] = dataset
        if state:
            data['state'] = state
        if memory:
            data['memory'] = memory
        if tombstone:
            data['tombstone'] = tombstone
        if tag_dict:
            for k, v in tag_dict.items():
                data['tag.' + str(k)] = v
        if credentials:
            data['credentials'] = True
        if limit:
            data['limit'] = limit
        else:
            limit = 1000
        if offset:
            data['offset'] = offset
        else:
            offset = 0
        machines = []
        while True:
            j, r = self.request('GET', 'machines', params=data)
            machines.extend(j)
            if not paged:
                query_limit = r.headers['x-query-limit']
                resource_count = r.headers['x-resource-count']
                if resource_count < query_limit:
                    data['offset'] += data['limit']
                else: 
                    break
            else:
                break
        return [Machine(data_dict=m, datacenter=self) for m in machines]
    

class Machine(object):
    def __init__(self, data_dict=None, datacenter=None, machine_id=None):
        self.id = machine_id or data_dict.pop('id')
        self.datacenter = datacenter
        if not data_dict:
            data_dict = self.datacenter.raw_machine_data(self.id)
        if data_dict:
            self.name = data_dict.get('name')
            self.type = data_dict.get('type')
            self.state = data_dict.get('state')
            self.dataset = data_dict.get('dataset')
            self.memory = data_dict.get('memory')
            self.disk = data_dict.get('disk')
            self.ips = data_dict.get('ips', [])
            self.metadata = data_dict.get('metadata', {})
            self.created = data_dict.get('created')
            self.updated = data_dict.get('updated')
    
    def __str__(self):
        return self.id
    
    
