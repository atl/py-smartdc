Tutorial
========

This is an example session as a mini-tutorial on SmartDC's most striking 
features. 

Datacenters and setting up a connection
---------------------------------------

We begin by importing the library and initializing the DataCenter, which is 
effectively our persistent connection object::

    from smartdc import DataCenter, DEBUG_CONFIG
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', 
                      secret='~/.ssh/id_rsa', config=DEBUG_CONFIG)

The ``key_id`` is the only parameter that requires user input. It has the form 
``/<username>/keys/<key_name>`` with the ``key_name`` being the label attached 
to the Public SSH key uploaded to your Smart Data Center 
(https://my.joyentcloud.com) account (and corresponding to the private key 
identified in the ``secret`` parameter). By default, ``py-smartdc`` looks for 
an ``ssh-agent``, and then your private ssh key at the above-listed path. The 
``DEBUG_CONFIG`` echoes each CloudAPI connection to ``stderr`` to aid in 
debugging. 

Once connected to a datacenter, you can look at all sorts of account 
information, such as listing your uploaded public SSH keys::

    sdc.keys()
    
Given one datacenter, you can connect to another with your existing 
credentials and preferences::

    east = sdc.datacenter('us-east-1')

While we're setting up, let's save a boot script for later upload::

    with open('./test-script.sh', 'w') as f:
        f.write('#!/usr/bin/sh\n\ntouch /home/admin/FTW\n')

Packages and datasets
---------------------

You can list packages and datasets available at a given datacenter::

    east.datasets()

Packages, datasets and most other CloudAPI entities are returned as dicts or 
lists of dicts. You can extract the unique identifiers pointing to these 
entities from these representations or pass the dicts themselves to methods 
that refer to these entities. The name, id, or URN -- as appropriate -- is 
extracted and passed to the CloudAPI.

Identifying individual datasets, as it turns out, doesn't require a fully 
qualified URN: the CloudAPI currently appears to be clever enough to resolve 
an ambiguous URN to the most recent one. Handy.

::

    latest64 = east.dataset('sdc:sdc:smartos64:')

``py-smartdc`` defines a few convenience functions beyond the ones offering 
raw results directly from the CloudAPI, such as filtering through available 
packages or datasets to return the default assigned by the datacenter::

    east.default_package()

...or locally filtering for packages or datasets that match a regular 
expression::

    sdc.packages('high[- ]cpu')
    
    east.datasets('smartos(64)?:')

Instantiating machines
----------------------

Sometimes we can create a smartmachine with no arguments at all: a default 
dataset and a default package are usually defined by the datacenter, and a 
unique name will always be defined if you omit one. However, besides valuing 
convenience and terseness, this python package is also about exercising fine 
control::

    test_machine = east.create_machine(name='test-machine', dataset=latest64,
                    package='Small 1GB', boot_script='./test-script.sh', 
                    tags={'type':'test'})

Note that this illustrates some of the flexibility of py-smartdc. The 
``dataset`` parameter happens to be the ``dict`` we got from by querying the 
CloudAPI, but the ``create_machine`` method extracts the appropriate URN from 
the ``dict``. More conventionally, the ``package`` parameter is identified by 
a string, the name of the bundle of machine resources. We upload the 
previously-saved ``boot_script``, and add a tag to the machine, so we can quickly 
identify test instances.

.. Note:: Although boot scripts are tremendously useful, in testing, we've 
   discovered that the SMF service that runs the boot script will kill processes
   that exceed 60 seconds execution time, so this is not necessarily 
   the best vehicle for long ``pkgin`` installations, for example.

This method call instantiates a ``smartdc.machine.Machine`` object that has 
its own methods and properties that allow you to examine data about the remote 
machine controlled via CloudAPI. Many methods correspond with the HTTP API 
driving it, but there are additional convenience methods here, as well.

For example, ``poll_while`` and ``poll_until`` block while continually polling 
the datacenter for the machine's ``.state`` to be updated. Note that if you 
model the state transition wrongly (or don't trigger a state change 
correctly), these methods can block in an infinite loop. We can also change 
the wait interval (from a default of 2 seconds) if we're feeling particularly 
impatient or conscientious.

::

    test_machine.poll_while('provisioning', interval=3)

The Machine object we are working with is the same as what would be 
instantiated when listing machines from the datacenter or directly 
instantiated on a :py:class:`smartdc.machine.Machine` object with a datacenter 
and id. When obtaining lists of machine resources from the Smart Data Center, 
the DataCenter object method returns instantiated Machine objects that are the 
same as those yielded by the freshly created machines. You can quickly 
demonstrate this to yourself by searching for the new machine amongst the 
datacenter's machines::

    test_machine == east.machines(name='test-machine')[0]

Interacting with running instances
----------------------------------

Now that we have both provisioned a machine and ensured that it is running, we 
can connect to it and perform some remote commands. In order to do this, we 
use the `ssh`_ package. SmartDC uses it internally to connect with an 
``ssh-agent`` if one is available. (For more extensive workflows, Fabric_, 
which shares most of SmartDC's dependencies, is commonly used, but we don't 
use it for this illustrative tutorial.)

We find the user-accessible IP address using the ``public_ips`` property of 
our machine instance. We use the key that we know works with the Smart Data 
Center, and connect using the ``admin`` account::

    import ssh
    
    ssh_conn = ssh.SSHClient()
    
    ssh_conn.set_missing_host_key_policy(ssh.AutoAddPolicy())
    
    ssh_conn.connect(test_machine.public_ips[0], username='admin')

We can list the installed packages, and trivially parse them into 
id-description pairs::

    _, rout, _ = ssh_conn.exec_command('pkgin ls')
    
    dict(ln.split(None,1) for ln in rout)

Let's take a look to see if the boot script fired::

    print ssh_conn.exec_command('ls')[1].read()

Close the connection, stop the machine, wait until stopped, and delete the 
machine::

    ssh_conn.close()
    
    test_machine.stop()
    
    test_machine.poll_until('stopped')
    
    test_machine.delete()

Advanced example
----------------

If you have accumulated many test instances in a datacenter and you need to 
shut them all down quickly, you might consider the following use of a thread 
pool. This particular example usage is predicated upon the machines being 
given a common tag.

::

    from operator import methodcaller
    from multiprocessing.dummy import Pool
    
    simultaneous = Pool(min(east.num_machines(tags={'type':'test'}), 8))
    
    test_machines = east.machines(tags={'type':'test'})
    
    simultaneous.map(methodcaller('stop'), test_machines)
    
    simultaneous.map(methodcaller('poll_until','stopped'), test_machines)
    
    simultaneous.map(methodcaller('status'), test_machines)
    
    simultaneous.map(methodcaller('delete'), test_machines)
    
    east.num_machines(tags={'type':'test'}) == 0

To learn more, you can read the API documentation for both the `DataCenter`_ 
and `Machine`_ classes.

.. _ssh: https://github.com/bitprophet/ssh
.. _Fabric: http://docs.fabfile.org/
.. _DataCenter: http://packages.python.org/smartdc/datacenter.html
.. _Machine: http://packages.python.org/smartdc/machine.html
