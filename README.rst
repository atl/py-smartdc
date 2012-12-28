Python SmartDataCenter
======================

Connect with Joyent_'s SmartDataCenter CloudAPI_ via Python, using secure 
http-signature_ signed requests. It enables you to programmatically provision
and otherwise control machines within Joyent_'s public cloud.

This is a third-party effort.

This module currently supports:

* Secure connections (via http_signature_ and optionally, ssh-agent)
* Key management
* Browsing and access of datacenters, datasets (OS distributions/VM bundles), 
  and packages (machine sizes and resources)
* Machine listing, search, creation, management 
  (start/stop/reboot/resize/delete), snapshotting, metadata, and tags
* Installing boot scripts on machines

It attempts to provide Pythonic objects (for Data Centers, Machines and 
Snapshots) and convenience methods only when appropriate, and otherwise deals 
with string identifiers or dicts as lightweight objects.

Requirements
------------

* requests_
* http_signature_
* PyCrypto_ (required by http_signature)

Optional:

* ssh_  or paramiko_ (post-1.8.0) 
  (used by http_signature for its ``ssh-agent`` integration)

We assume that ``json`` is present because requests now requires py2.6 and 
up.

Python SmartDataCenter Links
----------------------------

* `Python SmartDataCenter Tutorial`_ 
* `smartdc in PyPI`_
* `http_signature in PyPI`_
* `py-smartdc at GitHub`_
* `py-http-signature at GitHub`_
* `py-smartdc Documentation`_ & API reference
* `Joyent CloudAPI Documentation`_

.. _Joyent: http://joyentcloud.com/
.. _CloudAPI: https://api.joyentcloud.com/docs
.. _Joyent CloudAPI Documentation: CloudAPI_
.. _http-signature: 
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md
.. _requests: http://pypi.python.org/pypi/requests
.. _PyCrypto: http://pypi.python.org/pypi/pycrypto
.. _ssh: http://pypi.python.org/pypi/ssh
.. _paramiko: http://pypi.python.org/pypi/paramiko
.. _Python SmartDataCenter Tutorial: 
    http://packages.python.org/smartdc/tutorial.html
.. _smartdc in PyPI: http://pypi.python.org/pypi/smartdc
.. _http_signature in PyPI: http://pypi.python.org/pypi/http_signature
.. _http_signature: `http_signature in PyPI`_
.. _py-http-signature at GitHub: https://github.com/atl/py-http-signature
.. _py-smartdc at GitHub: https://github.com/atl/py-smartdc
.. _py-smartdc Documentation: http://packages.python.org/smartdc/
.. _Telefónica's InstantServers: http://cloud.telefonica.com/instantservers/

Installation
------------

::

    pip install smartdc

Quickstart
----------

This requires a Joyent Public Cloud account with valid payment information and
at least one SSH key uploaded. The example as presented should cost a maximum
of 0.03USD::

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/accountname/keys/keyname')
    
    sdc.datasets()
    
    sm = sdc.create_machine(name='test', dataset='sdc:sdc:standard:',
          package='Extra Small 512 MB')
    
    sm.poll_until('running')
    
    import urllib2
    
    urllib2.urlopen('http://' + sm.public_ips[0]).headers.dict
    
    sm.stop()
    
    sm.poll_until('stopped')
    
    sm.delete()

Connecting with `Telefónica's InstantServers`_::

    from smartdc import DataCenter, TELEFONICA_LOCATIONS
    
    mad = DataCenter(location='eu-mad-1', 
                  known_locations=TELEFONICA_LOCATIONS,
                  key_id='/accountname/keys/keyname')
    
    mad.default_package()

Why?
----

A colleague and I wanted something Pythonic to fit into our preferred 
toolchain, and the easiest approach was to build it myself. Requests made some 
aspects stupidly easy, which is why I created the dependency for the first 
version. The colleague wanted integration with ``ssh-agent``, and using ssh_ 
was the easiest path to that.

Authors
-------

`Adam T. Lindsay`_

.. _Adam T. Lindsay: http://atl.me/

License
-------

MIT
