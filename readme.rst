Python SmartDataCenter
======================

Connect with Joyent_'s SmartDataCenter CloudAPI_ via Python, using secure 
http-signature_ signed requests.

This is a third-party effort.

This module currently supports:

* Secure connections (via py-http-signature_)
* Key management
* Browsing and access of datacenters, datasets (OS distributions/VM bundles), 
  and packages (machine sizes and resources)
* Machine listing, search, creation, management 
  (start/stop/reboot/resize/delete), snapshotting, metadata, and tags

It attempts to provide Pythonic objects (for Data Centers, Machines and 
Snapshots) and convenience methods only when appropriate, and otherwise deals 
with string identifiers or dicts as lightweight objects.

Requirements
------------

* requests_
* py-http-signature_
* PyCrypto_ (required by py-http-signature)
* (We assume that ``json`` is present because requests now requires py2.6 and 
  up.)

.. _Joyent: http://joyentcloud.com/
.. _CloudAPI: https://us-west-1.api.joyentcloud.com/docs
.. _http-signature: 
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md
.. _py-http-signature: https://github.com/atl/py-http-signature
.. _requests: https://github.com/kennethreitz/requests
.. _PyCrypto: http://pypi.python.org/pypi/pycrypto


Usage
-----

::

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', 
                      secret='~/.ssh/id_rsa')
    
    sdc.keys()
    
    sdc.datasets()
    
    east = sdc.datacenter('us-east-1')
    
    east.default_package()
    
    nu = east.create_image()
    
    nu.poll_while('provisioning')
    
    nu.state
    
    nu.stop()
    
    nu.poll_until('stopped')
    
    nu.delete()


Why?
----

A colleague and I wanted something Pythonic to fit into our preferred 
toolchain, and the easiest approach was to build it myself. Requests made some 
aspects stupidly easy, which is why I created the dependency for the first 
version.

License
-------

MIT
