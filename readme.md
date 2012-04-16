# Python SmartDataCenter

Connect with Joyent's SmartDataCenter CloudAPI via Python, using secure http-signature signed requests

## Requirements

* [requests](https://github.com/kennethreitz/requests)
* [py-http-signature](https://github.com/atl/py-http-signature)
* [PyCrypto](http://pypi.python.org/pypi/pycrypto)
* (We assume that `json` is present because requests now requires py2.6 and up.)

## Usage

    from smartdc import DataCenter
    
    sdc = DataCenter(location='us-sw-1', key_id='/test/keys/test_key', secret='~/.ssh/id_rsa')
    
    sdc.keys()
    
    sdc.datasets()
    
    east = sdc.datacenter('us-east-1')
    
    east.package('Small 1GB')

## License

MIT
