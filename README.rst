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

Python SmartDataCenter Links
----------------------------

* `smartdc in PyPI`_
* GitHub_ (atl/py-smartdc)
* `Python Documentation`_ & API reference
* `Joyent CloudAPI Documentation`_

.. _Joyent: http://joyentcloud.com/
.. _CloudAPI: https://api.joyentcloud.com/docs
.. _Joyent CloudAPI Documentation: CloudAPI_
.. _http-signature: 
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md
.. _py-http-signature: https://github.com/atl/py-http-signature
.. _requests: https://github.com/kennethreitz/requests
.. _PyCrypto: http://pypi.python.org/pypi/pycrypto
.. _smartdc in PyPI: http://pypi.python.org/pypi/smartdc
.. _GitHub: https://github.com/atl/py-smartdc
.. _Python Documentation: http://packages.python.org/smartdc/

Installation
------------

::

    pip install smartdc

Usage
-----

This is an example session::

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', 
                      secret='~/.ssh/id_rsa')

The `key_id` is the only non-guessable component. It has the form 
``/<username>/keys/<key_name>`` with the labels derived from your Smart Data 
Center (my.joyentcloud.com) account. By default, `py-smartdc` looks for your
private ssh key at the above-listed path.

Once connected to a datacenter, you can look at all sorts of account 
information, such as listing your uploaded public SSH keys::

    sdc.keys()
    
Given one datacenter, you can connect to another with your existing 
credentials and preferences::

    east = sdc.datacenter('us-east-1')
    
`py-smartdc` defines a few convenience functions beyond the ones connecting to 
the CloudAPI, such as filtering through all the packages or datasets to return 
the default assigned by the datacenter::

    east.default_package()

Packages, datasets and most other CloudAPI responses are returned as dicts or 
lists of dicts. You can extract the unique identifiers from these 
representations, or pass the dicts themselves to methods that refer to these 
entities.

Datasets, as it turns out, don't require a fully qualified URN: the CloudAPI 
currently appears to be clever enough to resolve an ambiguous URN to the most 
recent one.

::

    latest64 = east.dataset('sdc:sdc:smartos64:')

We can create a smartmachine with no arguments at all: a unique name, the default dataset and package are automatically defined. However, it helps to exercise a little control::

    test_machine = east.create_machine(name='test-machine', dataset=latest64)

There are convenience methods that block while continually polling the datacenter for the machine's `.state` to be updated. Note that if you model the state transition wrongly (or don't trigger a state change correctly), these methods can block in an infinite loop.

    test_machine.poll_while('provisioning')

Now that we have both provisioned a machine and ensured that it is running, we 
can connect to it and list the installed packages. In order to do this, we use 
`ssh`_, a fork of `paramiko` and a dependency of `fab`. After a 
``pip install ssh`` at the command line, we can continue with making a 
connection. We use our default auto-located key that we have proven to be updated at the Smart Data Center, and connect to the `admin` account::

    import ssh
    
    ssh_conn = ssh.SSHClient()
    
    ssh_conn.set_missing_host_key_policy(ssh.AutoAddPolicy())
    
    ssh_conn.connect(test_machine.public_ips[0], username='admin')

Many users would probably continue using `fab`, but for this example, we want to take the minimal approach. We can list the installed packages, and trivially parse them into id-description pairs::

    _,rout,_ = ssh_conn.exec_command('pkgin ls')
    
    dict(ln.split(None,1) for ln in rout)

Close the connection, stop the machine, wait until stopped, and delete the machine::

    ssh_conn.close()
    
    test_machine.stop()
    
    test_machine.poll_until('stopped')
    
    test_machine.delete()

.. _ssh: https://github.com/bitprophet/ssh

Why?
----

A colleague and I wanted something Pythonic to fit into our preferred 
toolchain, and the easiest approach was to build it myself. Requests made some 
aspects stupidly easy, which is why I created the dependency for the first 
version.

License
-------

MIT
