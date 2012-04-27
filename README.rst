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

We assume that ``json`` is present because requests now requires py2.6 and 
up. Although the tutorial uses the ``ssh`` package, there is no dependency by
``py-smartdc`` on it.

Python SmartDataCenter Links
----------------------------

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

Usage
-----

This is an example session as mini-tutorial. Import the library and initialize 
the DataCenter, which is effectively our persistent connection object::

    from smartdc import DataCenter, DEBUG_CONFIG
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', 
                      secret='~/.ssh/id_rsa', config=DEBUG_CONFIG)

The ``key_id`` is the only parameter that requires user input. It has the form 
``/<username>/keys/<key_name>`` with the ``key_name`` being the label attached 
to the Public SSH key uploaded to your Smart Data Center (my.joyentcloud.com) 
account (and corresponding to the private key identified in the ``secret`` 
parameter). By default, ``py-smartdc`` looks for your private ssh key at the 
above-listed path. The ``DEBUG_CONFIG`` echoes each CloudAPI connection to 
``stderr`` to aid in debugging. 

Once connected to a datacenter, you can look at all sorts of account 
information, such as listing your uploaded public SSH keys::

    sdc.keys()
    
Given one datacenter, you can connect to another with your existing 
credentials and preferences::

    east = sdc.datacenter('us-east-1')
    
``py-smartdc`` defines a few convenience functions beyond the ones connecting 
to the CloudAPI, such as filtering through all the packages or datasets to 
return the default assigned by the datacenter::

    east.default_package()

Packages, datasets and most other CloudAPI entities are returned as dicts or 
lists of dicts. You can extract the unique identifiers pointing to these 
entities from these representations or pass the dicts themselves to methods 
that refer to these entities. The name, id, or urn -- as appropriate -- is 
extracted and passed to the CloudAPI.

Datasets, as it turns out, don't require a fully qualified URN: the CloudAPI 
currently appears to be clever enough to resolve an ambiguous URN to the most 
recent one. Handy.

::

    latest64 = east.dataset('sdc:sdc:smartos64:')

Sometimes we can create a smartmachine with no arguments at all: a default 
dataset and a default package are usually defined by the datacenter, and a 
unique name will also be defined if you omit one. However, this python package 
is also about exercising fine control::

    test_machine = east.create_machine(name='test-machine', dataset=latest64
                    package='Small 1GB')

This instantiates a ``smartdc.Machine`` object that has its own methods and
properties that allow you to examine data about the remote machine controlled 
via CloudAPI. Many methods correspond with the HTTP API driving it, but there 
are also convenience methods here, as well.

For example, ``poll_while`` and ``poll_until`` block while continually polling 
the datacenter for the machine's ``.state`` to be updated. Note that if you 
model the state transition wrongly (or don't trigger a state change 
correctly), these methods can block in an infinite loop. We can also change 
the wait interval (from a default of 2 seconds) if we're feeling particularly 
impatient or conscientious.

::

    test_machine.poll_while('provisioning', interval=1)

This Machine object is the same as what would be instantiated when listing 
machines from the datacenter. When obtaining lists of machine resources from
the Smart Data Center, the DataCenter object method returns instantiated 
Machine objects that are the same as those that are freshly created. You can 
quickly demonstrate this to yourself by searching for the new machine amongst
the datacenter's machines::

    test_machine == east.machines(name='test-machine')[0]

Now that we have both provisioned a machine and ensured that it is running, we 
can connect to it and list the installed packages. In order to do this, (for 
the purposes of this tutorial, only) we use the `ssh`_ package, which is a 
fork of ``paramiko`` and a dependency of ``fab``. After a 

    pip install ssh 

...at the command line, we can continue with making a connection. We can find 
a user-accessible IP address using the ``public_ips`` property of our machine 
instance. We use the key that we know works with the Smart Data Center, and 
connect using the ``admin`` account::

    import ssh
    
    ssh_conn = ssh.SSHClient()
    
    ssh_conn.set_missing_host_key_policy(ssh.AutoAddPolicy())
    
    ssh_conn.connect(test_machine.public_ips[0], username='admin')

We can list the installed packages, and trivially parse them into 
id-description pairs::

    _, rout, _ = ssh_conn.exec_command('pkgin ls')
    
    dict(ln.split(None,1) for ln in rout)

Close the connection, stop the machine, wait until stopped, and delete the 
machine::

    ssh_conn.close()
    
    test_machine.stop()
    
    test_machine.poll_until('stopped')
    
    test_machine.delete()

If you have accumulated many test instances in a datacenter and you need to 
shut them all down quickly, you might consider the following use of a thread 
pool::

    from operator import methodcaller
    from multiprocessing.dummy import Pool
    
    simultaneous = Pool(east.num_machines())
    all_machines = east.machines()
    
    simultaneous.map(methodcaller('stop'), all_machines)
    
    simultaneous.map(methodcaller('poll_until','stopped'), all_machines)
    
    simultaneous.map(methodcaller('status'), all_machines)
    
    simultaneous.map(methodcaller('delete'), all_machines)
    
    east.num_machines() == 0

To learn more, you can read the API documentation for both the `DataCenter`_ 
and `Machine`_ objects.

.. _ssh: https://github.com/bitprophet/ssh
.. _DataCenter: http://packages.python.org/smartdc/datacenter.html
.. _Machine: http://packages.python.org/smartdc/machine.html

Why?
----

A colleague and I wanted something Pythonic to fit into our preferred 
toolchain, and the easiest approach was to build it myself. Requests made some 
aspects stupidly easy, which is why I created the dependency for the first 
version.

Authors
-------

`Adam T. Lindsay`_

.. _Adam T. Lindsay: http://atl.me/

License
-------

MIT
