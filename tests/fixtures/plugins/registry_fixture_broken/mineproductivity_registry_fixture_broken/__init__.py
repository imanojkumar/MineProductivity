"""Registry Framework test fixture: a deliberately broken plugin.

Importing this module always raises -- proves
``EntryPointDiscovery.discover()`` isolates one bad entry-point's import
failure from every other entry-point in the same group (design spec
§11, §26).
"""

raise RuntimeError("intentionally broken fixture plugin: for isolation testing only")
