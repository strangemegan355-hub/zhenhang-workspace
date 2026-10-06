"""The quote domain's public surface.

Only modules that outside callers may import belong here. The package `__init__` must stay free of
imports: a submodule import executes it, so anything imported here becomes part of every caller's
import chain — which is how a cycle appeared the first time this surface was written.
"""
