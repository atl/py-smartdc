# Python SmartDataCenter

Connect with Joyent's SmartDataCenter CloudAPI via Python, using secure http-signature signed requests

## Requirements

* requests
* py-http-signature
* PyCrypto
* json

## Usage

    from smartdc import DataCenterConnection
    
    sdc = DataCenterConnection(key_id='/test/keys/test_key', secret='~/.ssh/id_rsa')
    
    sdc.keys()

## License

MIT
