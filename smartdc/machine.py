import time
from datetime import datetime


def priv(x): 
    """
    Incomplete heuristic to find an IP on a private network
    """
    return x.startswith((u'192.168.', u'10.', u'172.'))


def pub(x):
    """
    Not private
    """
    return not priv(x)


def dt_time(x):
    """
    Somewhat cheap hack to parse ISO8601 as returned from API
    """
    return datetime.strptime(x.rpartition('+')[0], "%Y-%m-%dT%H:%M:%S")


def timestamp(x): 
    """
    Convert ISO8601 into a UNIX timestamp (via dt_time)
    """
    return calendar.timegm(dt_time(x).timetuple())


class Machine(object):
    """
    A local proxy representing the state of a remote CloudAPI machine.
    
    A Machine object is intended to be a convenient container for methods and 
    data relevant to a remotely running compute node managed by CloudAPI. A 
    Machine is tied to a DataCenter object, and makes all its requests via 
    that interface. It does not attempt to manage the state cache in most 
    cases, instead requiring the user to explicitly update with a refresh() 
    call.
    """
    def __init__(self, datacenter, machine_id=None, data=None):
        """
        Typically, a Machine object is instantiated automatically by a
        DataCenter object, but a user may instantiate one with a minimum
        of a 'datacenter' object and a unique ID according to the machine. 
        If data is passed in to instantiate, then the init method takes 
        in the dict and populates its internal values from that.
        """
        self.id = machine_id or data.pop('id')
        self.datacenter = datacenter
        if not data:
            data = self.datacenter.raw_machine_data(self.id)
        self._save(data)
    
    def __str__(self):
        """
        Represents the Machine by its unique ID as a string.
        """
        return self.id
    
    def __repr__(self):
        """
        Presents a readable representation.
        """
        if self.datacenter:
            dc = str(self.datacenter)
        else:
            dc = '<None>'
        return '<{module}.{cls}: <{name}> in {dc}>'.format(
            module=self.__module__, cls=self.__class__.__name__, 
            name=self.name, dc=dc)
    
    def _save(self, data):
        """
        Take the data from a dict and commit them to appropriate attributes.
        """
        self.name = data.get('name')
        self.type = data.get('type')
        self.state = data.get('state')
        self.dataset = data.get('dataset')
        self.memory = data.get('memory')
        self.disk = data.get('disk')
        self.ips = data.get('ips', [])
        self.metadata = data.get('metadata', {})
        self.created = dt_time(data.get('created'))
        self.updated = dt_time(data.get('updated'))
    
    def refresh(self):
        """
        GET /:login/machines/:id
        
        Fetch the existing state and values for the Machine from the 
        DataCenter and commit the values locally.
        """
        data = self.datacenter.raw_machine_data(self.id)
        self._save(data)
    
    @property
    def path(self):
        """
        Convenience property to insert the id into a relative path for 
        requests.
        """
        return 'machines/{id}'.format(id=self.id)
    
    @property
    def public_ips(self):
        """
        Filter through known IP addresses for the machine to return a list of
        public IPs.
        """
        return filter(pub, self.ips)
    
    @property
    def private_ips(self):
        """
        Filter through known IP addresses for the machine to return a list of
        private IPs.
        """
        return filter(priv, self.ips)
    
    def stop(self):
        """
        POST /:login/machines/:id?action=stop
        
        Initiate shutdown of the remote machine.
        """
        action = {'action': 'stop'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def start(self):
        """
        POST /:login/machines/:id?action=start
        
        Initiate boot of the remote machine.
        """
        action = {'action': 'start'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def reboot(self):
        """
        POST /:login/machines/:id?action=reboot
        
        Initiate reboot of the remote machine.
        """
        action = {'action': 'reboot'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def resize(self, package):
        """
        POST /:login/machines/:id?action=resize
        
        Initiate resizing of the remote machine to a new package.
        """
        if isinstance(package, dict):
            package = package['name']
        action = {'action': 'resize',
                  'package': package}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def status(self):
        """
        GET /:login/machines/:id
        
        Refresh the machine's information by fetching it remotely, then 
        returning the state as a string.
        """
        self.refresh()
        return self.state
    
    def delete(self):
        """
        DELETE /:login/machines/:id
        
        Initiate deletion of a stopped remote machine.
        """
        j, r = self.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    @classmethod
    def create_in_datacenter(cls, datacenter, **kwargs):
        """
        POST /:login/machines
        
        Class method, provided as a convenience. 
        Provision a machine in the current DataCenter, returning an 
        instantiated Machine() object. All of the parameter values are 
        optional, as they are assigned default values by the Datacenter's API 
        itself. 
        
        'datacenter' is the only required argument. The rest of the arguments 
        are passed to the DataCenter object as with 
        DataCenter.create_machine():
        
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
        return datacenter.create_machine(**kwargs)
    
    def poll_until(self, state, interval=2):
        """
        GET /:login/machines/:id
        
        Convenience method that continuously polls the current state of the 
        machine remotely, and returns until the named 'state' argument is 
        reached. The default wait 'interval' between requests is 2 seconds, 
        but it may be changed.
        
        Note that if the next state is wrongly identified, this method may
        loop forever.
        """
        while self.status() != state:
            time.sleep(interval)
    
    def poll_while(self, state, interval=2):
        """
        GET /:login/machines/:id
        
        Convenience method that continuously polls the current state of the 
        machine remotely, and returns while the machine has the named 'state' 
        argument. Once the state changes, the method returns. The default wait 
        'interval' between requests is 2 seconds, but it may be changed.
        
        Note that if a state transition has not correctly been triggered, this
        method may loop forever.
        """
        while self.status() == state:
            time.sleep(interval)
    
    def get_metadata(self):
        """
        GET /:login/machines/:id/metadata
        
        Fetch and return the metadata dict for the machine. The method 
        refreshes the locally cached copy of the metadata kept in the 
        'metadata' attribute and returns it.
        """
        j, _ = self.datacenter.request('GET', self.path + '/metadata')
        self.metadata = j
        return j
    
    def update_metadata(self, **kwargs):
        """
        POST /:login/machines/:id/metadata
        
        Send an metadata dict update for the machine (following dict.update() 
        semantics). The method also refreshes the locally cached copy of the 
        metadata kept in the 'metadata' attribute and returns it.
        """
        j, _ = self.datacenter.request('POST', self.path + '/metadata', 
                    params=kwargs)
        self.metadata = j
        return j
    
    def delete_metadata_at_key(self, key):
        """
        DELETE /:login/machines/:id/metadata/:key
        
        Deletes the Machine metadata contained at 'key'. Also explicitly 
        requests and returns the Machine metadata so that the local copy stays 
        synchronized.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/metadata/' + 
                    key)
        r.raise_for_status()
        return self.get_metadata()
    
    def delete_all_metadata(self):
        """
        DELETE /:login/machines/:id/metadata
        
        Deletes all the metadata stored for this Machine. Also explicitly 
        requests and returns the Machine metadata so that the local copy stays 
        synchronized.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/metadata')
        r.raise_for_status()
        return self.get_metadata()
    
    def get_tags(self):
        """
        GET /:login/machines/:id/tags
        
        Returns the complete set of tags for this machine as a dict. A local 
        copy is not kept because these are essentially search keys.
        """
        j, _ = self.datacenter.request('GET', self.path + '/tags')
        return j
    
    def add_tags(self, **kwargs):
        """
        POST /:login/machines/:id/tags
        
        Appends the tags (expressed as arbitrary keyword arguments) to those 
        already set for the Machine.
        """
        j, _ = self.datacenter.request('POST', self.path + '/tags', 
            params=kwargs)
        return j
    
    def get_tag(self, tag):
        """
        GET /:login/machines/:id/tags/:tag
        
        Returns a the value for a single tag as text.
        """
        headers = {'Accept': 'text/plain'}
        j, _ = self.datacenter.request('GET', self.path + '/tags/' + tag)
        return j
    
    def delete_tag(self, tag):
        """
        DELETE /:login/machines/:id/tags/:tag
        
        Delete a tag and its corresponding value on the Machine.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/tags/' + tag)
        r.raise_for_status()
    
    def delete_all_tags(self):
        """
        DELETE /:login/machines/:id/tags/:tag
        
        Delete all tags and their corresponding values on the Machine.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/tags')
        r.raise_for_status()
    
    def raw_snapshot_data(self, name):
        """
        GET /:login/machines/:id/snapshots/:name
        
        Used internally to get a raw dict of a single machine snapshot.
        """
        j, _ = self.datacenter.request('GET', self.path + '/snapshots/' + 
                str(name))
        return j
    
    def snapshots(self):
        """
        GET /:login/machines/:id/snapshots
        
        Lists all snapshots for the Machine, returning a list of Snapshot 
        objects.
        """
        j, _ = self.datacenter.request('GET', self.path + '/snapshots')
        return [Snapshot(machine=self, data=s) for s in j]
    
    def create_snapshot(self, name):
        """
        POST /:login/machines/:id/snapshots
        
        Create a snapshot for this machine with the given 'name'. Returns a 
        single Snapshot object.
        """
        params = {'name': name}
        j, _ = self.datacenter.request('POST', self.path + '/snapshots', 
            params=params)
        return Snapshot(machine=self, data=j, name=name)
    
    def start_from_snapshot(self, name):
        """
        POST /:login/machines/:id/snapshots/:name
        
        Start the machine from a snapshot with the given 'name'.
        """
        _, r = self.datacenter.request('POST', self.path + '/snapshots/' + 
            str(name))
        r.raise_for_status()
        return self
    
    def snapshot(self, name):
        """
        GET /:login/machines/:id/snapshots/:name
        
        Return a Snapshot object that already exists for the machine, 
        identified by 'name'.
        """
        return Snapshot(machine=self, name=name)
    

class Snapshot(object):
    """
    A local proxy representing the current state of a machine snapshot.
    
    A Snapshot object is intended to be a convenient container for a 
    snapshot's state and for performing methods on it.
    """
    def __init__(self, machine, name=None, data=None):
        """
        Typically, a snapshot object is instantiated automatically by 
        creating or listing snapshots for a Machine. However, a snapshot may
        be manually instantiated by giving a 'machine' and a 'name' as 
        parameters, and the snapshot's state and other data will be queried
        from the server.
        """
        self.name = name or data.pop('name')
        self.machine = machine
        if not data:
            data = self.machine.raw_snapshot_data(self.name)
        self._save(data)
    
    def __str__(self):
        """
        The compact representation of a Snapshot is its name as a string.
        """
        return self.name
    
    def __repr__(self):
        """
        Presents a readable representation.
        """
        return '<{module}.{cls}: <{name}> on <Machine: {mach}>>'.format(
            module=self.__module__, cls=self.__class__.__name__, 
            name=self.name, mach=str(self.machine.name))
    
    def _save(self, data):
        """
        Take the data from a dict and commit them to appropriate attributes.
        """
        self.state = data.get('state')
        self.created = dt_time(data.get('created'))
        self.updated = dt_time(data.get('updated'))
    
    @property
    def path(self):
        """
        Convenience property to insert the id into a relative path for 
        requests.
        """
        return self.machine.path + '/snapshots/' + self.name
    
    def refresh(self):
        """
        GET /:login/machines/:id/snapshots/:name
        
        Fetch the existing state and values for the Snapshot 
        and commit the values locally.
        """
        data = self.machine.raw_snapshot_data(self.name)
        self._save(data)
    
    def status(self):
        """
        GET /:login/machines/:id/snapshots/:name
        
        Refresh the snapshot's information by fetching it remotely, then 
        returning the state as a string.
        """
        self.refresh()
        return self.state
    
    def delete(self):
        """
        DELETE /:login/machines/:id/snapshots/:name
        
        Deletes the snapshot from the machine.
        """
        _, r = self.machine.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    def start(self):
        """
        POST /:login/machines/:id/snapshots/:name
        
        Initiate boot of the machine from this snapshot.
        """
        _, r = self.machine.datacenter.request('POST', self.path)
        r.raise_for_status()
        return self.machine
    
