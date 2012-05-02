import time
from datetime import datetime

__all__ = ['Machine', 'Snapshot']

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
    
    A :py:class:`smartdc.machine.Machine` object is intended to be a 
    convenient container for methods and data relevant to a remotely running 
    compute node managed by CloudAPI. A :py:class:`smartdc.machine.Machine` is 
    tied to a :py:class:`smartdc.datacenter.DataCenter` object, and makes all 
    its requests via that interface. It does not attempt to manage the state 
    cache in most cases, instead requiring the user to explicitly update with 
    a :py:meth:`refresh` call.
    """
    def __init__(self, datacenter, machine_id=None, data=None, 
            credentials=False):
        """
        :param datacenter: datacenter that contains this machine
        :type datacenter: :py:class:`smartdc.datacenter.DataCenter`
        
        :param machine_id: unique ID of the machine
        :type machine_id: :py:class:`basestring`
        
        :param data: raw data for instantiation
        :type data: :py:class:`dict`
        
        :param credentials: whether credentials should be returned
        :type credentials: :py:class:`bool`
        
        Typically, a :py:class:`smartdc.machine.Machine` object is 
        instantiated automatically by a 
        :py:class:`smartdc.datacenter.DataCenter` object, but a user may 
        instantiate one with a minimum of a `datacenter` parameter and a 
        unique ID according to the machine. The object then pulls in the
        machine data from the datacenter API. If `data` is passed in to  
        instantiate, then ingest the dict and populate internal values from 
        that.
        
        All of the following attributes are read-only:
        
        :var name: human-readable label for the machine
        :var id: identifier for the machine
        :var type: type (`smartmachine` or `virtualmachine`) of the 
            machine
        :var state: last-known state of the machine
        :var dataset: the machine template
        :var memory: the RAM (MiB) allocated for the machine 
            (:py:class:`int`\)
        :var disk: the persistent storage (MiB) allocated for the 
            machine (:py:class:`int`\)
        :var ips: :py:class:`list` of IPv4 addresses for the machine
        :var metadata: :py:class:`dict` of user-generated attributes for 
            the machine
        :var created: :py:class:`datetime.datetime` of machine creation 
            time
        :var updated: :py:class:`datetime.datetime` of machine update 
            time
        """
        self.id = machine_id or data.pop('id')
        self.datacenter = datacenter
        """the :py:class:`smartdc.datacenter.DataCenter` object that holds 
        this machine"""
        if not data:
            data = self.datacenter.raw_machine_data(self.id, 
                    credentials=credentials)
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
    
    def __eq__(self, other):
        if isinstance(other, dict):
            return self.id == other.get('id')
        elif isinstance(other, Machine):
            return self.id == other.id
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
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
        if not hasattr(self, '_credentials'):
            self._credentials = {}
        self._credentials.update(self.metadata.pop('credentials', {}))
        self.boot_script = self.metadata.pop('user-script', None)
        self.created = dt_time(data.get('created'))
        self.updated = dt_time(data.get('updated'))
    
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
    
    @classmethod
    def create_in_datacenter(cls, datacenter, **kwargs):
        """
        ::
        
            POST /:login/machines
        
        Class method, provided as a convenience. 
        
        :param datacenter: datacenter for creating the machine
        :type datacenter: :py:class:`smartdc.datacenter.DataCenter`
        
        Provision a machine in the current 
        :py:class:`smartdc.datacenter.DataCenter`, returning an 
        instantiated :py:class:`smartdc.machine.Machine` object. All of the 
        parameter values are optional, as they are assigned default values by 
        the Datacenter's API itself. 
        
        'datacenter' is the only required argument. The rest of the arguments 
        are passed to the DataCenter object as with 
        :py:meth:`smartdc.datacenter.DataCenter.create_machine`.
        """
        return datacenter.create_machine(**kwargs)
    
    def refresh(self, credentials=False):
        """
        ::
        
            GET /:login/machines/:id
        
        :param credentials: whether to return machine passwords
        :type credentials: :py:class:`bool`
        
        Fetch the existing state and values for the 
        :py:class:`smartdc.machine.Machine` from the datacenter and commit the 
        values locally.
        """
        data = self.datacenter.raw_machine_data(self.id, 
                credentials=credentials)
        self._save(data)
    
    def credentials(self):
        """
        ::
        
            GET /:login/machines/:id?credentials=True
        
        :Returns: known login-password pairs for the machine
        :rtype: :py:class:`dict`
        
        Provisionally re-fetch the machine information with the credentials 
        flag enabled.
        """
        if not self._credentials:
            self.refresh(credentials=True)
        return self._credentials
    
    def status(self):
        """
        ::
        
            GET /:login/machines/:id
        
        :Returns: the current machine state
        :rtype: :py:class:`basestring`
        
        Refresh the machine's information by fetching it remotely, then 
        returning the :py:attr:`state` as a string.
        """
        self.refresh()
        return self.state
    
    def stop(self):
        """
        ::
        
            POST /:login/machines/:id?action=stop
        
        Initiate shutdown of the remote machine.
        """
        action = {'action': 'stop'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def start(self):
        """
        ::
        
            POST /:login/machines/:id?action=start
        
        Initiate boot of the remote machine.
        """
        action = {'action': 'start'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def reboot(self):
        """
        ::
        
            POST /:login/machines/:id?action=reboot
        
        Initiate reboot of the remote machine.
        """
        action = {'action': 'reboot'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def resize(self, package):
        """
        ::
        
            POST /:login/machines/:id?action=resize
        
        Initiate resizing of the remote machine to a new package.
        """
        if isinstance(package, dict):
            package = package['name']
        action = {'action': 'resize',
                  'package': package}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def delete(self):
        """
        ::
        
            DELETE /:login/machines/:id
        
        Initiate deletion of a stopped remote machine.
        """
        j, r = self.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    def poll_until(self, state, interval=2):
        """
        ::
        
            GET /:login/machines/:id
        
        :param state: target state
        :type state: :py:class:`basestring`
        
        :param interval: pause in seconds between polls
        :type interval: :py:class:`int`
        
        Convenience method that continuously polls the current state of the 
        machine remotely, and returns until the named `state` argument is 
        reached. The default wait `interval` between requests is 2 seconds, 
        but it may be changed.
        
        .. Note:: If the next state is wrongly identified, this method may
            loop forever.
        """
        while self.status() != state:
            time.sleep(interval)
    
    def poll_while(self, state, interval=2):
        """
        ::
        
            GET /:login/machines/:id
        
        :param state: (assumed) current state
        :type state: :py:class:`basestring`
        
        :param interval: pause in seconds between polls
        :type interval: :py:class:`int`
        
        Convenience method that continuously polls the current state of the 
        machine remotely, and returns while the machine has the named `state` 
        argument. Once the state changes, the method returns. The default wait 
        `interval` between requests is 2 seconds, but it may be changed.
        
        .. Note:: If a state transition has not correctly been triggered, this
            method may loop forever.
        """
        while self.status() == state:
            time.sleep(interval)
    
    def get_metadata(self):
        """
        ::
        
            GET /:login/machines/:id/metadata
        
        :Returns: machine metadata
        :rtype: :py:class:`dict`
        
        Fetch and return the metadata dict for the machine. The method 
        refreshes the locally cached copy of the metadata kept in the 
        :py:attr:`metadata` attribute and returns it.
        """
        j, _ = self.datacenter.request('GET', self.path + '/metadata')
        self.metadata = j
        return j
    
    def update_metadata(self, **kwargs):
        """
        ::
        
            POST /:login/machines/:id/metadata
        
        :Returns: current metadata
        :rtype: :py:class:`dict`
        
        Send an metadata dict update for the machine (following dict.update() 
        semantics) using the keys and values passed in the keyword arguments. 
        The method also refreshes the locally cached copy of the metadata kept 
        in the :py:attr:`metadata` attribute and returns it.
        """
        j, _ = self.datacenter.request('POST', self.path + '/metadata', 
                    data=kwargs)
        self.metadata = j
        return j
    
    def delete_metadata_at_key(self, key):
        """
        ::
        
            DELETE /:login/machines/:id/metadata/:key
        
        :param key: identifier for matadata entry
        :type key: :py:class:`basestring`
        
        :Returns: current metadata
        :rtype: :py:class:`dict`
        
        Deletes the machine metadata contained at 'key'. Also explicitly 
        requests and returns the machine metadata so that the local copy stays 
        synchronized.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/metadata/' + 
                    key)
        r.raise_for_status()
        return self.get_metadata()
    
    def set_boot_script(self, filename):
        """
        ::
        
            POST /:login/machines/:id/metadata
        
        :param filename: file path to the script to be uploaded and executed
            at boot on the machine
        :type filename: :py:class:`basestring`
        
        Replace the existing boot script for the machine with the data in the 
        named file.

        .. Note:: The SMF service that runs the boot script will kill processes
           that exceed 60 seconds execution time, so this is not necessarily 
           the best vehicle for long ``pkgin`` installations, for example.
        """
        data = {}
        with open(filename) as f:
            data['user-script'] = f.read()
        j, r = self.datacenter.request('POST', self.path + '/metadata', 
                    data=data)
        r.raise_for_status()
        self.boot_script = data['user-script']
    
    def delete_boot_script(self):
        """
        ::
        
            DELETE /:login/machines/:id/metadata/user-script
        
        Deletes any existing boot script on the machine.
        """
        j, r = self.datacenter.request('DELETE', self.path + 
                '/metadata/user-script')
        r.raise_for_status()
        self.boot_script = None
    
    def delete_all_metadata(self):
        """
        ::
        
            DELETE /:login/machines/:id/metadata
        
        :Returns: current metadata
        :rtype: empty :py:class:`dict`
        
        Deletes all the metadata stored for this machine. Also explicitly 
        requests and returns the machine metadata so that the local copy stays 
        synchronized.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/metadata')
        r.raise_for_status()
        return self.get_metadata()
    
    def get_tags(self):
        """
        ::
        
            GET /:login/machines/:id/tags
        
        :Returns: complete set of tags for this machine
        :rtype: :py:class:`dict` 
        
        A local copy is not kept because these are essentially search keys.
        """
        j, _ = self.datacenter.request('GET', self.path + '/tags')
        return j
    
    def add_tags(self, **kwargs):
        """
        ::
        
            POST /:login/machines/:id/tags
        
        Appends the tags (expressed as arbitrary keyword arguments) to those 
        already set for the machine.
        """
        j, _ = self.datacenter.request('POST', self.path + '/tags', 
            data=kwargs)
        return j
    
    def get_tag(self, tag):
        """
        ::
        
            GET /:login/machines/:id/tags/:tag
        
        :Returns: the value for a single tag
        :rtype: :py:class:`basestring`
        """
        headers = {'Accept': 'text/plain'}
        j, _ = self.datacenter.request('GET', self.path + '/tags/' + tag)
        return j
    
    def delete_tag(self, tag):
        """
        ::
        
            DELETE /:login/machines/:id/tags/:tag
        
        Delete a tag and its corresponding value on the machine.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/tags/' + tag)
        r.raise_for_status()
    
    def delete_all_tags(self):
        """
        ::
        
            DELETE /:login/machines/:id/tags
        
        Delete all tags and their corresponding values on the machine.
        """
        j, r = self.datacenter.request('DELETE', self.path + '/tags')
        r.raise_for_status()
    
    def raw_snapshot_data(self, name):
        """
        ::
        
            GET /:login/machines/:id/snapshots/:name
        
        :param name: identifier for snapshot
        :type name: :py:class:`basestring`
        
        :rtype: :py:class:`dict`
        
        Used internally to get a raw dict of a single machine snapshot.
        """
        j, _ = self.datacenter.request('GET', self.path + '/snapshots/' + 
                str(name))
        return j
    
    def snapshots(self):
        """
        ::
        
            GET /:login/machines/:id/snapshots
        
        :rtype: :py:class:`list` of :py:class:`smartdc.machine.Snapshot`
        
        Lists all snapshots for the Machine.
        """
        j, _ = self.datacenter.request('GET', self.path + '/snapshots')
        return [Snapshot(machine=self, data=s) for s in j]
    
    def create_snapshot(self, name):
        """
        ::
        
            POST /:login/machines/:id/snapshots
        
        :param name: identifier for snapshot
        :type name: :py:class:`basestring`
        
        :rtype: :py:class:`smartdc.machine.Snapshot`
        
        Create a snapshot for this machine's current state with the given 
        `name`.
        """
        params = {'name': name}
        j, _ = self.datacenter.request('POST', self.path + '/snapshots', 
            data=params)
        return Snapshot(machine=self, data=j, name=name)
    
    def start_from_snapshot(self, name):
        """
        ::
        
            POST /:login/machines/:id/snapshots/:name
        
        :param name: identifier for snapshot
        :type name: :py:class:`basestring`
        
        Start the machine from the snapshot with the given 'name'.
        """
        _, r = self.datacenter.request('POST', self.path + '/snapshots/' + 
            str(name))
        r.raise_for_status()
        return self
    
    def snapshot(self, name):
        """
        ::
        
            GET /:login/machines/:id/snapshots/:name
        
        :param name: identifier for snapshot
        :type name: :py:class:`basestring`
        
        :rtype: :py:class:`smartdc.machine.Snapshot`
        
        Return a snapshot that already exists for the machine, identified by 
        `name`.
        """
        return Snapshot(machine=self, name=name)
    

class Snapshot(object):
    """
    A local proxy representing the current state of a machine snapshot.
    
    A :py:class:`smartdc.machine.Snapshot` object is intended to be a 
    convenient container for a snapshot's state and for performing methods on 
    it.
    """
    def __init__(self, machine, name=None, data=None):
        """
        :param machine: source of the snapshot
        :type machine: :py:class:`smartdc.machine.Machine`
        
        :param name: identifier for snapshot
        :type name: :py:class:`basestring`
        
        :param data: raw data for instantiation
        :type data: :py:class:`dict`
        
        Typically, a :py:class:`smartdc.machine.Snapshot` object is 
        instantiated automatically by creating or listing snapshots for a 
        :py:class:`smartdc.machine.Machine`. However, a snapshot may be 
        manually instantiated by giving a 'machine' and a 'name' as 
        parameters, and the snapshot's state and other data will be queried
        from the server.
        
        The following attributes are read-only:
        
        :var name: human-readable label for the machine
        :var state: last-known state of the machine
        :var created: :py:class:`datetime.datetime` of machine creation 
            time
        :var updated: :py:class:`datetime.datetime` of machine update 
            time
        
        """
        self.name = name or data.pop('name')
        self.machine = machine
        """:py:class:`smartdc.machine.Machine` object that contains this 
        snapshot"""
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
        ::
        
            GET /:login/machines/:id/snapshots/:name
        
        Fetch the existing state and values for the snapshot 
        and commit the values locally.
        """
        data = self.machine.raw_snapshot_data(self.name)
        self._save(data)
    
    def status(self):
        """
        ::
        
            GET /:login/machines/:id/snapshots/:name
        
        :Returns: the current state
        :rtype: :py:class:`basestring`
        
        Refresh the snapshot's information by fetching it remotely, then 
        returning the :py:attr:`state` as a string.
        """
        self.refresh()
        return self.state
    
    def delete(self):
        """
        ::
        
            DELETE /:login/machines/:id/snapshots/:name
        
        Deletes the snapshot from the machine.
        """
        _, r = self.machine.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    def start(self):
        """
        ::
        
            POST /:login/machines/:id/snapshots/:name
        
        :Returns: self
        
        Initiate boot of the machine from this snapshot.
        """
        _, r = self.machine.datacenter.request('POST', self.path)
        r.raise_for_status()
        return self.machine
    
