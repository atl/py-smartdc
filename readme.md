# Python SmartDataCenter

Connect with [Joyent](http://joyentcloud.com/)'s SmartDataCenter
[CloudAPI](https://us-west-1.api.joyentcloud.com/docs) via Python, 
using secure http-signature signed requests.

This is a third-party effort.

## Requirements

* [requests](https://github.com/kennethreitz/requests)
* [py-http-signature](https://github.com/atl/py-http-signature)
* [PyCrypto](http://pypi.python.org/pypi/pycrypto) (required by py-http-signature)
* (We assume that `json` is present because requests now requires py2.6 and up.)

## Usage

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', secret='~/.ssh/id_rsa')
    
    sdc.keys()
    
    sdc.datasets()
    
    east = sdc.datacenter('us-east-1')
    
    east.package('Small 1GB')
    
    nu = east.create_image()
    
    import time
    
    while nu.status() == 'provisioning':
        time.sleep(2)
        print '.',
    
    nu.stop()
    
    while nu.status() != 'stopped':
        time.sleep(2)
        print '.',
    
    nu.delete()


## Why?

A colleague and I wanted something Pythonic to fit into our preferred toolchain, and 
the easiest approach was to build it myself. Requests made some aspects stupidly easy, 
which is why I created the dependency for the first version.

## License

MIT
