import sys
import json
from operator import itemgetter

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
    'X-Api-Version':  API_VERSION,
    'User-Agent':    'py-smartdc'
}

DEBUG_CONFIG = {'verbose': sys.stderr}

class DataCenter(object):
    """
    Basic connection object that makes all API requests.
    
    The DataCenter is the basic connection unit with the CloudAPI, and it
    maintains the data it requires for further requests. It lazily updates 
    some internal data as and when the user requests it, and only
    accesses the REST API on internal function calls.
    """
    def __init__(self, location=None, key_id=None, secret=None, 
                headers=None, login=None, config=None, known_locations=None):
        """
        A DataCenter object may be instantiated without any parameters, but
        practically speaking, the 'key_id' and 'secret' parameters are 
        necessary before any meaningful requests may be made. 
        
        The 'location' parameter is notionally a hostname, but it may be 
        expressed as an FQDN, one of the keys to the 'known_locations' dict, 
        or, as a fallback, a bare hostname as prefix to the API_HOST_SUFFIX.
        
        The default location is 'us-west-1', because that is where 
        'api.joyentcloud.com' redirects to at the time of writing. 
        
        Custom 'headers' that are inserted upon every request may be specified 
        as a dict. 
        
        The 'login' parameter reflects the user's path. 
        
        The 'config' dict is as with Requests, and DEBUG_CONFIG, which echoes 
        every request to stderr, is pre-defined as a convenience. 
        
        The 'known_locations' parameter may be given a keys-to-URLs mapping, 
        allowing one to customize access to a private cloud.
        """
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
        """
        Short representation of a DataCenter.
        """
        if self.login != 'my':
            user_string = self.login + '@'
        else:
            user_string = ''
        return '<{cls}: {user_string}{location}>'.format(
            cls=self.__class__.__name__,
            user_string=user_string, location=self.location)
    
    def __repr__(self):
        """
        Representation of a DataCenter as a string.
        """
        if self.login != 'my':
            user_string = '<{0}> '.format(self.login)
        else:
            user_string = ''
        return '<{module}.{cls}: {name}at <{loc}>>'.format(
            module=self.__module__, cls=self.__class__.__name__, 
            name=user_string, loc=self.location)
        
    @property
    def url(self):
        return '{base_url}/{login}/'.format(base_url=self.base_url, 
            login=self.login)
    
    def authenticate(self, key_id=None, secret=None):
        """
        If no 'key_id' or 'secret' were entered on initialization, or there is
        a need to change the existing authentication credentials, one may 
        authenticate with a 'key_id' and 'secret'.
        """
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret)
    
    def request(self, method, path, headers=None, **kwargs):
        """
        Modify requests slightly passing via the Requests base 'request'
        method.
        
        Input is a path, rather then a full URL, and default headers and 
        authentication are inserted.
        
        Output is a tuple of the response body (decoded according to 
        content-type) and the requests object itself. Client (4xx) errors are 
        raised immediately.
        """
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
        """
        GET /
        
        Returns a programmatically-generated API summary using HTTP verbs and 
        URL templates.
        """
        resp = requests.request('GET', self.base_url)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            return json.loads(resp.content)
    
    def keys(self):
        """
        GET /:login/keys
        
        Returns a list of all public keys on record (each represented within a 
        dict) for the authenticated account.
        """
        j, _ = self.request('GET', 'keys')
        return j
    
    def key(self, key_id):
        """
        GET /:login/keys/:key
        
        Retrieves an individual key record (represented as key-values within a 
        dict) based on the 'key_id'.
        """
        j, _ = self.request('GET', 'keys/' + str(key_id))
        return j
    
    def add_key(self, key_id, key):
        """
        POST /:login/keys
        
        Uploads a new OpenSSH key to SmartDataCenter for use in SSH and HTTP 
        signing, where 'key_id' is the name, and 'key' is the key in text.
        """
        data = json.dumps({'name': str(key_id), 'key': str(key)})
        j, _ = self.request('POST', 'keys', data=data)
        return j
    
    def delete_key(self, key_id):
        """
        DELETE /:login/keys/:key
        
        Deletes an SSH key from the server by 'key_id'.
        """
        j, r = self.request('DELETE', 'keys/' + str(key_id))
        r.raise_for_status()
        return j
    
    def me(self):
        """
        GET /:login
        
        Returns basic information about the authenticated account.
        """
        j, _ = self.request('GET', '')
        if 'login' in j and self.login == 'my':
            self.login = j['login']
        return j
    
    def datacenters(self):
        """
        GET /:login/datacenters
        
        Returns a dict of all datacenters (mapping from short location key to 
        full URL) that this cloud is aware of. Updates the local 
        'known_locations' based upon this information.
        """
        j, _ = self.request('GET', 'datacenters')
        self.known_locations.update(j)
        return j
    
    def datacenter(self, name):
        """
        Returns a new DataCenter object, treating the 'name' argument as a 
        location key, and keeping existing authentication and other 
        configurations on this object.
        """
        # The base form of this, as below, simply sets up a redirect. 
        # j, _ = self.request('GET', 'datacenters/' + str(name))
        dc = DataCenter(location=name, headers=self.default_headers, 
                login=self.login, config=self.config)
        dc.auth = self.auth
        return dc
    
    def datasets(self):
        """
        GET /:login/datasets
        
        Provides a list of datasets (OS templates) available in this 
        datacenter, represented as a dict.
        """
        j, _ = self.request('GET', 'datasets')
        return j
    
    def default_dataset(self):
        """
        GET /:login/datasets
        
        Requests all the datasets in this datacenter, filters for the default, 
        and returns a single dict.
        """
        return filter(itemgetter('default'), self.datasets())[0]
    
    def dataset(self, dataset_id):
        """
        GET /:login/datasets/:id
        
        Gets a single dataset identified by the unique ID or URN. URNs are 
        also prefix-matched. If passed a dict that contains an 'urn' or 'id' 
        key, it uses the respective value as the identifier.
        """
        if isinstance(dataset_id, dict):
            dataset_id = dataset_id.get('urn', dataset_id['id'])
        j, _ = self.request('GET', 'datasets/' + str(dataset_id))
        return j
    
    def packages(self):
        """
        GET /:login/packages
        
        Returns a list of packages (machine "sizes", as a dict of resource 
        types and values) available in this datacenter.
        """
        j, _ = self.request('GET', 'packages')
        return j
    
    def default_package(self):
        """
        GET /:login/packages
        
        Requests all the packages in this datacenter, filters for the default, 
        and returns a single dict.
        """
        return filter(itemgetter('default'), self.datasets())[0]
    
    def package(self, name):
        """
        GET /:login/packages/:package
        
        Gets a dict representing resource values for a package by name. If 
        passed a dict containing a 'name' key, it uses the corresponding 
        value.
        """
        if isinstance(name, dict):
            name = name['name']
        j, _ = self.request('GET', 'packages/' + str(name))
        return j
    
    def num_machines(self):
        """
        HEAD /:login/machines
        
        Returns a count of the number of machines present at this datacenter
        via a HEAD request.
        """
        _, r = self.request('HEAD', 'machines')
        num = r.headers.get('x-resource-count', 0)
        return int(num)
    
    def raw_machine_data(self, machine_id):
        """
        GET /:login/machines/:machine
        
        Primarily used internally to get a raw dict of a single machine.
        """
        if isinstance(machine_id, dict):
            machine_id = machine_id['id']
        j, _ = self.request('GET', 'machines/' + str(machine_id))
        return j
    
    def machines(self, machine_type=None, name=None, dataset=None, state=None, 
            memory=None, tombstone=None, tag_dict=None, credentials=False, 
            paged=False, limit=None, offset=None):
        """
        GET /:login/machines
        
        Query for machines in the current DataCenter matching the input 
        criteria, returning a list of instantiated Machine() objects. 
        
        Basic filter criteria include 'machine_type', 'name', 'dataset', 
        'state', and 'memory'. 
        
        'tombstone' allows you to query for machines destroyed in the last N 
        minutes. 
        
        'tag_dict' accepts a dict of keys and values to query upon in the 
        machine's tag space. 
        
        'credentials' is a flag that signals whether to return the created 
        credentials in the query.
        
        'limit' and 'offset' are the REST API's raw paging mechanism. 
        Alternatively, one can let 'paged' remain False, and let the method 
        call attempt to collect all of the machines.
        """
        params = {}
        if machine_type:
            params['type'] = machine_type
        if name:
            params['name'] = name
        if dataset:
            if isinstance(dataset, dict):
                dataset = dataset.get('urn', dataset['id'])
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
                    data['offset'] = (params.get('offset', offset) + 
                                      params.get('limit', limit)    )
                else:
                    break
            else:
                break
        return [Machine(datacenter=self, data=m) for m in machines]
    
    def create_machine(self, name=None, package=None, dataset=None,
            metadata_dict=None, tag_dict=None):
        """
        POST /:login/machines
        
        Provision a machine in the current DataCenter, returning an 
        instantiated Machine() object. All of the parameter values are 
        optional, as they are assigned default values by the Datacenter's API 
        itself.
        
        'name' is a string used as a humab-readable label for the machine.
        
        'package' is a cluster of resource values identified by name. If 
        passed a dict containing a 'name' key, it uses the corresponding 
        value.
        
        'dataset' is base OS image identified by a globally unique ID or URN. 
        If passed a dict containing an 'urn' or 'id' key, it uses the 
        corresponding value. The server API appears to resolve incomplete or
        ambiguous URNs with the highest version number.
        
        'metadata_dict' and 'tag_dict' are optionally passed dicts containing
        arbitrary key-value pairs. A guideline for determining between the two 
        is that tags may be used as filters when querying for and listing 
        machines, while a metadata dict is returned when requesting details of 
        a machine.
        """
        params = {}
        if name:
            params['name'] = name
        if package:
            if isinstance(package, dict):
                package = package['name']
            params['package'] = package
        if dataset:
            if isinstance(dataset, dict):
                dataset = dataset.get('urn', dataset['id'])
            params['dataset'] = dataset
        if metadata_dict:
            for k, v in metadata_dict.items():
                params['metadata.' + str(k)] = v
        if tag_dict:
            for k, v in tag_dict.items():
                params['tag.' + str(k)] = v
        j, r = self.request('POST', 'machines', params=params)
        return Machine(datacenter=self, data=j)
    
    def machine(self, machine_id):
        """
        GET /:login/machines/:id
        
        Return a Machine object already present in the datacenter, identified 
        by 'machine_id', its unique ID.
        """
        if isinstance(machine_id, dict):
            machine_id = machine_id['id']
        elif isinstance(machine_id, Machine):
            machine_id = machine_id.id
        return Machine(datacenter=self, machine_id=machine_id)
    

