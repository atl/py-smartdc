import time
from datetime import datetime


def priv(x): 
    return x.startswith((u'192.168.', u'10.', u'172.'))


def pub(x): 
    return not priv(x)


def dt_time(x): 
    return datetime.strptime(x.rpartition('+')[0], "%Y-%m-%dT%H:%M:%S")


def timestamp(x): 
    return calendar.timegm(dt_time(x).timetuple())


class Machine(object):
    def __init__(self, data=None, datacenter=None, machine_id=None):
        self.id = machine_id or data.pop('id')
        self.datacenter = datacenter
        if not data:
            data = self.datacenter.raw_machine_data(self.id)
        self._save(data)
    
    def __str__(self):
        return self.id
    
    def __repr__(self):
        if self.datacenter:
            dc = str(self.datacenter)
        else:
            dc = '<None>'
        return '<{module}.{cls}: <{name}> in {dc}>'.format(module=self.__module__,
            cls=self.__class__.__name__, name=self.name, dc=dc)
    
    def _save(self, data):
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
        data = self.datacenter.raw_machine_data(self.id)
        self._save(data)
    
    @property
    def path(self):
        return 'machines/{id}'.format(id=self.id)
    
    @property
    def public_ips(self):
        return filter(pub, self.ips)
    
    @property
    def private_ips(self):
        return filter(priv, self.ips)
    
    def stop(self):
        action = {'action': 'stop'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def start(self):
        action = {'action': 'start'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def reboot(self):
        action = {'action': 'reboot'}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def resize(self, package):
        if isinstance(package, dict):
            package = package['name']
        action = {'action': 'resize',
                  'package': package}
        j, r = self.datacenter.request('POST', self.path, params=action)
        r.raise_for_status()
    
    def status(self):
        self.refresh()
        return self.state
    
    def delete(self):
        j, r = self.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    @classmethod
    def create_in_datacenter(cls, datacenter, **kwargs):
        return datacenter.create_machine(**kwargs)
    
    def poll_until(self, state, interval=2):
        while self.status() != state:
            time.sleep(interval)
    
    def poll_while(self, state, interval=2):
        while self.status() == state:
            time.sleep(interval)
    
    def get_metadata(self):
        j, _ = self.datacenter.request('GET', self.path + '/metadata')
        self.metadata = j
        return j
    
    def update_metadata(self, **kwargs):
        j, _ = self.datacenter.request('POST', self.path + '/metadata', params=kwargs)
        self.metadata = j
        return j
    
    def delete_metadata_at_key(self, key):
        j, r = self.datacenter.request('DELETE', self.path + '/metadata/' + key)
        r.raise_for_status()
        return self.get_metadata()
    
    def delete_all_metadata(self):
        j, r = self.datacenter.request('DELETE', self.path + '/metadata')
        r.raise_for_status()
        return self.get_metadata()
    
    def get_tags(self):
        j, _ = self.datacenter.request('GET', self.path + '/tags')
        return j
    
    def add_tags(self, **kwargs):
        j, _ = self.datacenter.request('POST', self.path + '/tags', params=kwargs)
        return j
    
    def get_tag(self, tag):
        headers = {'Accept': 'text/plain'}
        j, _ = self.datacenter.request('GET', self.path + '/tags/' + tag)
        return j
    
    def delete_tag(self, tag):
        j, r = self.datacenter.request('DELETE', self.path + '/tags/' + tag)
        r.raise_for_status()
    
    def delete_all_tags(self):
        j, r = self.datacenter.request('DELETE', self.path + '/tags')
        r.raise_for_status()
    
    def raw_snapshot_data(self, name):
        j, _ = self.datacenter.request('GET', self.path + '/snapshots/' + str(name))
        return j
    
    def snapshots(self):
        j, _ = self.datacenter.request('GET', self.path + '/snapshots')
        return [Snapshot(machine=self, data=s) for s in j]
    
    def create_snapshot(self, name):
        params = {'name': name}
        j, _ = self.datacenter.request('POST', self.path + '/snapshots', params=params)
        return Snapshot(machine=self, data=j, name=name)
    
    def start_from_snapshot(self, name):
        _, r = self.datacenter.request('POST', self.path + '/snapshots/' + str(name))
        r.raise_for_status()
        return self
    

class Snapshot(object):
    def __init__(self, machine=None, data=None, name=None):
        self.name = name or data.pop('name')
        self.machine = machine
        if not data:
            data = self.machine.raw_snapshot_data(self.name)
        self._save(data)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return '<{module}.{cls}: <{name}> on <Machine: {mach}>>'.format(module=self.__module__,
            cls=self.__class__.__name__, name=self.name, mach=str(self.machine.name))
    
    def _save(self, data):
        self.state = data.get('state')
        self.created = dt_time(data.get('created'))
        self.updated = dt_time(data.get('updated'))
    
    @property
    def path(self):
        return self.machine.path + '/snapshots/' + self.name
    
    def refresh(self):
        data = self.machine.raw_snapshot_data(self.name)
        self._save(data)
    
    def status(self):
        self.refresh()
        return self.state
    
    def delete(self):
        _, r = self.machine.datacenter.request('DELETE', self.path)
        r.raise_for_status()
    
    def start(self):
        _, r = self.machine.datacenter.request('POST', self.path)
        r.raise_for_status()
        return self.machine
    
