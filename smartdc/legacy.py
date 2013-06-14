from __future__ import print_function
from .datacenter import *

class LegacyDataCenter(DataCenter):
    API_VERSION = '~6.5'
    
    def api(self):
        raise RuntimeError('Method no longer supported by SDC')
    

    