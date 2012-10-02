import sys
import json
from operator import itemgetter
import re

import requests
from http_signature.requests_auth import HTTPSignatureAuth

from .machine import Machine

__all__ = ['DataCenter', 'DEBUG_CONFIG', 'KNOWN_LOCATIONS', 
            'DEFAULT_LOCATION']

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


def search_dicts(dicts, predicate, fields):
    matcher = re.compile(predicate, re.IGNORECASE)
    for d in dicts:
        m = [d for f in fields if matcher.search(d.get(f, ''))]
        if m:
            yield m[0]
            continue


class DataCenter(object):
    """
    Basic connection object that makes all API requests.
    
    The :py:class:`smartdc.datacenter.DataCenter` is the basic connection unit 
    with the CloudAPI, and it maintains the data it requires for further 
    requests. It lazily updates some internal data as and when the user 
    requests it, and only accesses the REST API on method calls (never on 
    attribute access).
    """
    def __init__(self, location=None, key_id=None, secret='~/.ssh/id_rsa', 
                headers=None, login=None, config=None, known_locations=None,
                allow_agent=False):
        """
        A :py:class:`smartdc.datacenter.DataCenter` object may be instantiated 
        without any parameters, but practically speaking, the `key_id` and 
        `secret` parameters are necessary before any meaningful requests may 
        be made. 
        
        :param location: SmartDC API's hostname
        :type location: :py:class:`basestring`
        
        :param key_id: SmartDC identifier for the ssh key
        :type key_id: :py:class:`basestring`
        
        :param secret: path to private rsa key (default: '~/.ssh/id_rsa')
        :type secret: :py:class:`str`
        
        :param headers: headers inserted upon every request
        :type headers: :py:class:`dict`
        
        :param login: user path in SmartDC
        :type login: :py:class:`basestring`
        
        :param config: Requests-style configuration
        :type config: :py:class:`dict`
        
        :param known_locations: keys-to-URLs mapping used by `location` 
        :type known_locations: :py:class:`dict`
        
        :param allow_agent: whether or not to try ssh-agent
        :type allow_agent: :py:class:`bool`
        
        The `location` is notionally a hostname, but it may be 
        expressed as an FQDN, one of the keys to the `known_locations` dict, 
        or, as a fallback, a bare hostname as prefix to the API_HOST_SUFFIX.
        The default location is 'us-west-1', because that is where 
        'api.joyentcloud.com' redirects to at the time of writing.
        
        The `known_locations` dict allows for custom access to a private 
        cloud.
        
        Attributes:
        
        :var location: location of the machine
        :var known_locations: :py:class:`dict` of known locations for this 
            cluster of datacenters
        :var login: user path in the SmartDC
        """
        self.location = location or DEFAULT_LOCATION
        self.known_locations = known_locations or KNOWN_LOCATIONS
        self.config = config or {}
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret,
                allow_agent=allow_agent)
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
        Representation of a DataCenter as a :py:class:`str`.
        """
        if self.login != 'my':
            user_string = '<{0}> '.format(self.login)
        else:
            user_string = ''
        return '<{module}.{cls}: {name}at <{loc}>>'.format(
            module=self.__module__, cls=self.__class__.__name__, 
            name=user_string, loc=self.location)
    
    def __eq__(self, other):
        """
        Not all DataCenters are created equal.
        """
        if isinstance(other, DataCenter):
            if self.login == 'my':
                self.me()
            if other.login == 'my':
                other.me()
            return self.url == other.url
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @property
    def url(self):
        """Base URL for SmartDC requests"""
        return '{base_url}/{login}/'.format(base_url=self.base_url, 
            login=self.login)
    
    @property
    def base_url(self):
        """Protocol + hostname"""
        if self.location in self.known_locations:
            return self.known_locations[self.location]
        elif '.' in self.location or self.location == 'localhost':
            return 'https://' + self.location
        else:
            return 'https://' + self.location + API_HOST_SUFFIX
    
    def authenticate(self, key_id=None, secret=None, allow_agent=False):
        """
        :param key_id: SmartDC identifier for the ssh key
        :type key_id: :py:class:`basestring`
        
        :param secret: path to private rsa key
        :type secret: :py:class:`basestring`
        
        :param allow_agent: whether or not to try ssh-agent
        :type allow_agent: :py:class:`bool`
        
        If no `key_id` or `secret` were entered on initialization, or there is
        a need to change the existing authentication credentials, one may 
        authenticate with a `key_id` and `secret`.
        """
        if key_id and secret:
            self.auth = HTTPSignatureAuth(key_id=key_id, secret=secret, 
                allow_agent=allow_agent)
    
    def request(self, method, path, headers=None, data=None, **kwargs):
        """
        (Primarily) internal method for making all requests to the datacenter.
        
        :param method: HTTP verb
        :type method: :py:class:`str`
        
        :param path: path relative to `login` path
        :type path: :py:class:`str`
        
        :param headers: additional headers to send
        :type headers: :py:class:`dict`
        
        :Returns: tuple of decoded response body & `Response` object
        :raises: client (4xx) errors
        """
        full_path = self.url + path
        request_headers = {}
        request_headers.update(self.default_headers)
        if headers:
            request_headers.update(headers)
        jdata = None
        if data:
            jdata = json.dumps(data)
        resp = requests.request(method, full_path, auth=self.auth, 
            headers=request_headers, config=self.config, data=jdata,
            **kwargs)
        if (resp.status_code == 401 and self.auth and 
                self.auth.signer._agent_key):
            self.auth.signer.swap_keys()
            return self.request(method, path, headers=headers, data=data,
                **kwargs)
        if 400 <= resp.status_code < 499:
            if resp.content:
                print >> sys.stderr, resp.content
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
        ::
        
            GET /
        
        :Returns: a programmatically-generated API summary using HTTP verbs 
            and URL templates
        :rtype: :py:class:`dict`
        """
        resp = requests.request('GET', self.base_url)
        if 400 <= resp.status_code < 499:
            resp.raise_for_status()
        if resp.content:
            return json.loads(resp.content)
    
    def keys(self):
        """
        ::
        
            GET /:login/keys
        
        :Returns: all public keys on record for the authenticated account.
        :rtype: :py:class:`list` of :py:class:`dict`\s
        """
        j, _ = self.request('GET', 'keys')
        return j
    
    def key(self, key_id):
        """
        ::
        
            GET /:login/keys/:key
        
        :param key_id: identifier for an individual key record for the account
        :type key_id: :py:class:`basestring`
        
        :returns: details of the key
        :rtype: :py:class:`dict`
        """
        j, _ = self.request('GET', 'keys/' + str(key_id))
        return j
    
    def add_key(self, key_id, key):
        """
        ::
        
            POST /:login/keys
        
        :param key_id: label for the new key
        :type key_id: :py:class:`basestring`
        
        :param key: the full SSH RSA public key
        :type key: :py:class:`str`
        
        Uploads a public key to be added to the account's credentials.
        """
        data = {'name': str(key_id), 'key': str(key)}
        j, _ = self.request('POST', 'keys', data=data)
        return j
    
    def delete_key(self, key_id):
        """
        ::
        
            DELETE /:login/keys/:key
        
        :param key_id: identifier for an individual key record for the account
        :type key_id: :py:class:`basestring`
        
        Deletes an SSH key from the server identified by `key_id`.
        """
        j, r = self.request('DELETE', 'keys/' + str(key_id))
        r.raise_for_status()
        return j
    
    def me(self):
        """
        ::
        
            GET /:login
        
        :Returns: basic information about the authenticated account
        :rtype: :py:class:`dict`
        """
        j, _ = self.request('GET', '')
        if 'login' in j and self.login == 'my':
            self.login = j['login']
        return j
    
    def datacenters(self):
        """
        ::
        
            GET /:login/datacenters
        
        :Returns: all datacenters (mapping from short location key to 
            full URL) that this cloud is aware of
        :rtype: :py:class:`dict`
        
        This method also updates the local `known_locations` attribute based 
        upon this information.
        """
        j, _ = self.request('GET', 'datacenters')
        self.known_locations.update(j)
        return j
    
    def datacenter(self, name):
        """
        :param name: location key
        :type name: :py:class:`basestring`
        
        :Returns: a new DataCenter object
        
        This method treats the 'name' argument as a location key (on the 
        `known_locations` attribute dict) or FQDN, and keeps existing 
        authentication and other configuration from this object.
        """
        # The base form of this, as below, simply sets up a redirect. 
        # j, _ = self.request('GET', 'datacenters/' + str(name))
        dc = DataCenter(location=name, headers=self.default_headers, 
                login=self.login, config=self.config)
        dc.auth = self.auth
        return dc
    
    def datasets(self, search=None, fields=('description', 'urn')):
        """
        ::
        
            GET /:login/datasets
        
        :param search: optionally filter (locally) with a regular expression 
            search on the listed fields
        :type search: :py:class:`basestring` that compiles as a regular 
            expression
        
        :param fields: filter on the listed fields (defaulting to 
            ``description`` and ``urn``)
        :type fields: :py:class:`list` of :py:class:`basestring`\s
        
        :Returns: datasets (operating system templates) available in this 
            datacenter 
        :rtype: :py:class:`list` of :py:class:`dict`\s
        """
        j, _ = self.request('GET', 'datasets')
        if search:
            return list(search_dicts(j, search, fields))
        else:
            return j
    
    def default_dataset(self):
        """
        ::
        
            GET /:login/datasets
        
        :Returns: the default dataset for this datacenter
        :rtype: :py:class:`dict` or ``None``
        
        Requests all the datasets in this datacenter, filters for the default, 
        and returns the corresponding :py:class:`dict`, if a default has been 
        defined.
        """
        sets = filter(itemgetter('default'), self.datasets())
        if sets:
            return sets[0]
        else:
            return None
    
    def dataset(self, dataset_id):
        """
        ::
        
            GET /:login/datasets/:id
        
        :param dataset_id: unique ID or URN for a dataset
        :type dataset_id: :py:class:`basestring` or :py:class:`dict`
        
        :rtype: :py:class:`dict`
        
        Gets a single dataset identified by the unique ID or URN. URNs are 
        also prefix-matched. If passed a dict that contains an `urn` or `id` 
        key, it uses the respective value as the identifier.
        """
        if isinstance(dataset_id, dict):
            dataset_id = dataset_id.get('urn', dataset_id['id'])
        j, _ = self.request('GET', 'datasets/' + str(dataset_id))
        return j
    
    def packages(self, search=None, fields=('name',)):
        """
        ::
        
            GET /:login/packages
        
        :param search: optionally filter (locally) with a regular expression 
            search on the listed fields
        :type search: :py:class:`basestring` that compiles as a regular 
            expression
        
        :param fields: filter on the listed fields (defaulting to ``name``\)
        :type fields: :py:class:`list` of :py:class:`basestring`\s
        
        :Returns: packages (machine "sizes", with resource types and values) 
            available in this datacenter.
        :rtype: :py:class:`list` of :py:class:`dict`\s
        """
        j, _ = self.request('GET', 'packages')
        if search:
            return list(search_dicts(j, search, fields))
        else:
            return j
    
    def default_package(self):
        """
        ::
        
            GET /:login/packages
        
        :Returns: the default package for this datacenter
        :rtype: :py:class:`dict` or ``None``
        
        Requests all the packages in this datacenter, filters for the default, 
        and returns the corresponding dict, if a default has been defined.
        """
        packages = filter(itemgetter('default'), self.packages())
        if packages:
            return packages[0]
        else:
            return None
    
    def package(self, name):
        """
        ::
        
            GET /:login/packages/:package
        
        :param name: the name identifying the package
        :type dataset_id: :py:class:`basestring` or :py:class:`dict`
        
        :rtype: :py:class:`dict`
        
        Gets a dict representing resource values for a package by name. If 
        passed a dict containing a `name` key, it uses the corresponding 
        value.
        """
        if isinstance(name, dict):
            name = name['name']
        j, _ = self.request('GET', 'packages/' + str(name))
        return j
    
    def num_machines(self, machine_type=None, dataset=None, state=None, 
            memory=None, tombstone=None, tags=None):
        """
        ::
        
            HEAD /:login/machines
        
        Counts the number of machines total, or that match the predicates as
        with :py:meth:`machines`.
        
        :param machine_type: virtualmachine or smartmachine
        :type machine_type: :py:class:`basestring`
        
        :param dataset: unique ID or URN for a dataset
        :type dataset: :py:class:`basestring` or :py:class:`dict`
        
        :param state: current running state
        :type state: :py:class:`basestring`
        
        :param memory: current size of the RAM deployed for the machine (Mb)
        :type memory: :py:class:`int`
        
        :param tombstone: include machines destroyed in the last N minutes
        :type tombstone: :py:class:`int`
        
        :param tags: keys and values to query in the machines' tag space
        :type tags: :py:class:`dict`
        
        :Returns: a count of the number of machines (matching the predicates) 
            owned by the user at this datacenter
        :rtype: :py:class:`int`
        """
        _, r = self.request('HEAD', 'machines')
        num = r.headers.get('x-resource-count', 0)
        return int(num)
    
    def raw_machine_data(self, machine_id, credentials=False):
        """
        ::
        
            GET /:login/machines/:machine
        
        :param machine_id: identifier for the machine instance
        :type machine_id: :py:class:`basestring` or :py:class:`dict`
        
        :param credentials: whether the SDC should return machine credentials
        :type credentials: :py:class:`bool`
        
        :rtype: :py:class:`dict`
        
        Primarily used internally to get a raw dict for a single machine.
        """
        params = {}
        if isinstance(machine_id, dict):
            machine_id = machine_id['id']
        if credentials:
            params['credentials'] = True
        j, _ = self.request('GET', 'machines/' + str(machine_id), 
                params=params)
        return j
    
    def machines(self, machine_type=None, name=None, dataset=None, state=None, 
            memory=None, tombstone=None, tags=None, credentials=False, 
            paged=False, limit=None, offset=None):
        """
        ::
        
            GET /:login/machines
        
        Query for machines in the current DataCenter matching the input 
        criteria, returning a :py:class:`list` of instantiated 
        :py:class:`smartdc.machine.Machine` objects.
        
        :param machine_type: virtualmachine or smartmachine
        :type machine_type: :py:class:`basestring`
        
        :param name: machine name to find (will make the return list size 
            1 or 0)
        :type name: :py:class:`basestring`
        
        :param dataset: unique ID or URN for a dataset
        :type dataset: :py:class:`basestring` or :py:class:`dict`
        
        :param state: current running state
        :type state: :py:class:`basestring`
        
        :param memory: current size of the RAM deployed for the machine (Mb)
        :type memory: :py:class:`int`
        
        :param tombstone: include machines destroyed in the last N minutes
        :type tombstone: :py:class:`int`
        
        :param tags: keys and values to query in the machines' tag space
        :type tags: :py:class:`dict`
        
        :param credentials: whether to include the generated credentials for 
            machines, if present
        :type credentials: :py:class:`bool`
        
        :param paged: whether to return in pages
        :type paged: :py:class:`bool`
        
        :param limit: return N machines
        :type limit: :py:class:`int`
        
        :param offset: get the next `limit` of machines starting at this point
        :type offset: :py:class:`int`
        
        :rtype: :py:class:`list` of :py:class:`smartdc.machine.Machine`\s
        
        The `limit` and `offset` are the REST API's raw paging mechanism. 
        Alternatively, one can let `paged` remain `False`, and let the method 
        call attempt to collect all of the machines in multiple calls.
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
        if tags:
            for k, v in tags.items():
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
            metadata=None, tags=None, boot_script=None, credentials=False):
        """
        ::
        
            POST /:login/machines
        
        Provision a machine in the current 
        :py:class:`smartdc.datacenter.DataCenter`, returning an instantiated 
        :py:class:`smartdc.machine.Machine` object. All of the parameter 
        values are optional, as they are assigned default values by the 
        datacenter's API itself.
        
        :param name: a human-readable label for the machine
        :type name: :py:class:`basestring`
        
        :param package: cluster of resource values identified by name
        :type package: :py:class:`basestring` or :py:class:`dict`
        
        :param dataset: base operating system image identified by a globally 
            unique ID or URN
        :type dataset: :py:class:`basestring` or :py:class:`dict`
        
        :param metadata: keys & values with arbitrary supplementary 
            details for the machine, accessible from the machine itself
        :type metadata: :py:class:`dict`
        
        :param tags: keys & values with arbitrary supplementary 
            identifying information for filtering when querying for machines
        :type tags: :py:class:`dict`
        
        :param boot_script: path to a file to upload for execution on boot
        :type boot_script: :py:class:`basestring` as file path
        
        :rtype: :py:class:`smartdc.machine.Machine`
        
        If `package` or `dataset` are passed a :py:class:`dict` containing a 
        `name` key (in the case of `package`) or a `urn` or `id` key (in the 
        case of `dataset`), it passes the corresponding value. The server API 
        appears to resolve incomplete or ambiguous dataset URNs with the 
        highest version number.
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
        if metadata:
            for k, v in metadata.items():
                params['metadata.' + str(k)] = v
        if tags:
            for k, v in tags.items():
                params['tag.' + str(k)] = v
        if boot_script:
            with open(boot_script) as f:
                params['metadata.user-script'] = f.read()
        j, r = self.request('POST', 'machines', data=params)
        if r.status_code >= 400:
            print >> sys.stderr, j
            r.raise_for_status()
        return Machine(datacenter=self, data=j)
    
    def machine(self, machine_id, credentials=False):
        """
        ::
        
            GET /:login/machines/:id
        
        :param machine_id: unique identifier for a machine to be found in the 
            datacenter
        :type machine_id: :py:class:`basestring`
        
        :rtype: :py:class:`smartdc.machine.Machine`
        """
        if isinstance(machine_id, dict):
            machine_id = machine_id['id']
        elif isinstance(machine_id, Machine):
            machine_id = machine_id.id
        return Machine(datacenter=self, machine_id=machine_id, 
                credentials=credentials)
    

