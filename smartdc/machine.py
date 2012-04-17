import time

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
            dc = self.datacenter.location
        else:
            dc = 'None'
        return '<{module}.{cls}: <{name}> at <{loc}>>'.format(module=self.__module__,
            cls=self.__class__.__name__, name=self.name, loc=self.datacenter.location)
    
    def _save(self, data):
        self.name = data.get('name')
        self.type = data.get('type')
        self.state = data.get('state')
        self.dataset = data.get('dataset')
        self.memory = data.get('memory')
        self.disk = data.get('disk')
        self.ips = data.get('ips', [])
        self.metadata = data.get('metadata', {})
        self.created = data.get('created')
        self.updated = data.get('updated')
    
    def refresh(self):
        data = self.datacenter.raw_machine_data(self.id)
        self._save(data)
    
    @property
    def path(self):
        return 'machines/{id}'.format(id=self.id)
    
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

