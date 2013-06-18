from __future__ import print_function
from .datacenter import DataCenter

class LegacyDataCenter(DataCenter):
    """
    This class provides bare bones support for older versions of the 
    SmartDataCenter API.
    """
    API_VERSION = '~6.5'
    
    def api(self):
        raise RuntimeError('Method no longer supported by SDC')
    
    def packages(self, search=None, fields=('name',)):
        j, _ = self.request('GET', 'packages')
        if search:
            return list(search_dicts(j, search, fields))
        else:
            return j
    
    def default_package(self):
        packages = [pk for pk in self.packages() if pk.get('default')]
        if packages:
            return packages[0]
    
    def default_dataset(self):
        datasets = [ds for ds in self.datasets() if ds.get('default')]
        if datasets:
            return datasets[0]
    
    def images(self):
        raise RuntimeError('Method incompatible with legacy SDC mode')
    
    def image(self, *a, **k):
        raise RuntimeError('Method incompatible with legacy SDC mode')
    
    def networks(self):
        raise RuntimeError('Method incompatible with legacy SDC mode')
    
    def network(self, *a, **k):
        raise RuntimeError('Method incompatible with legacy SDC mode')
    
