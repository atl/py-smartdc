Changes
-------

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

