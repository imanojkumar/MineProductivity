"""Registry Framework test fixture: a well-behaved plugin.

Importing this module never raises -- ``EntryPointDiscovery.discover()``
must report this fixture's entry-point name as successfully loaded.
"""

IMPORTED = True
