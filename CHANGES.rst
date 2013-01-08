Changes
-------

0.1.12 (2013-01-08)
~~~~~~~~~~~~~~~~~~~
* Telefónica has updated the endpoints for its known locations. These locations are capable of SSL-verifiable connections.
* Move print statements in library to print functions (still pending issue with versioneer)
* Requests 1.0 release removed ``config`` from request's keyword arguments, so created a workaround that works in old and new versions
* ``verbose`` (bool) is now the preferred keyword argument in DataCenter initialization since we no longer piggy-back on requests config. ``config`` issues a warning.

0.1.11 (2012-12-07)
~~~~~~~~~~~~~~~~~~~
* Minor update to the README quickstart
* Machines are hashable based on their UUIDs
* Pre-programmed Telefónica locations are based on FQDNs
* KNOWN ISSUE: DataCenter equality not guaranteed with Telefónica servers (due to how they are identified by Telefónica)

0.1.10 (2012-11-07)
~~~~~~~~~~~~~~~~~~~
* This version accommodates communication with Telefónica's InstantServers service
* Change documentation to account for underlying shift in py-http-signature accommodating both (new) paramiko and ssh
* Add "verify" option to DataCenter to allow for opt-out of SSL Certificate verification (necessitated by Telefónica's initial release of InstantServers)
* Save more state from current DataCenter when transferring to another one
* Be a little more resourceful in resolving a DataCenter.datacenter() argument by name

0.1.9 (2012-10-02)
~~~~~~~~~~~~~~~~~~
* Bug fix: POSTs including data would get mangled while looking for a correct ssh-agent key (thanks, @thekad)
* Bug fix: ssh-agent would throw wrong error if it failed to find any keys
* Set `allow-agent` to False by default, thanks in part to this less-explored code path

0.1.8 (2012-05-02)
~~~~~~~~~~~~~~~~~~
* Bug fix: double-json encoding on add_key got in way of proper upload
* Introduce python-versioneer to hopefully make version management more palatable

0.1.7 (2012-05-01)
~~~~~~~~~~~~~~~~~~
* Renamed metadata_dict and tag_dict parameters to metadata and tags
* POST data as JSON, rather than encoded in URL
* Added boot_script option on machine creation
* Process and expose credentials
* Slight tutorial and other documentation cleanup
* Local filtering on datasets and packages

0.1.6 (2012-04-30)
~~~~~~~~~~~~~~~~~~
* Fixed release issues (README)
* Moved long tutorial out of the README
* Integrated with ``ssh-agent`` changes in ``http_signature``

