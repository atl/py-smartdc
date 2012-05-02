Python SmartDataCenter
======================

Connect with Joyent_'s SmartDataCenter CloudAPI_ via Python, using secure 
http-signature_ signed requests. It enables you to programmatically provision
and otherwise control machines within Joyent_'s public cloud.

This is a third-party effort.

This module currently supports:

* Secure connections (via py-http-signature_ and ssh-agent, when available)
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
* py-http-signature_
* PyCrypto_ (required by py-http-signature)
* ssh_ (used by py-http-signature for its ``ssh-agent`` integration)

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
.. _requests: https://github.com/kennethreitz/requests
.. _PyCrypto: http://pypi.python.org/pypi/pycrypto
.. _ssh: https://github.com/bitprophet/ssh
.. _Python SmartDataCenter Tutorial: 
    http://packages.python.org/smartdc/tutorial.html
.. _smartdc in PyPI: http://pypi.python.org/pypi/smartdc
.. _http_signature in PyPI: http://pypi.python.org/pypi/http_signature
.. _py-http-signature: `http_signature in PyPI`_
.. _py-http-signature at GitHub: https://github.com/atl/py-http-signature
.. _py-smartdc at GitHub: https://github.com/atl/py-smartdc
.. _py-smartdc Documentation: http://packages.python.org/smartdc/

Installation
------------

::

    pip install smartdc

Quickstart
----------

::

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key')
    
    sdc.datasets()
    
    sm = sdc.create_machine(name='test', dataset='sdc:sdc:smartosplus:',
          package='Small 1GB')
    
    sm.poll_until('running')
    
    import urllib2
    
    urllib2.urlopen('http://' + sm.public_ips[0]).headers.dict
    
    sm.stop()
    
    sm.poll_until('stopped')
    
    sm.delete()

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
