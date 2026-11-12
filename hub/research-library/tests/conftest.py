"""Keep the independent package suite separate from the broad legacy hub suite."""
from importlib.util import find_spec

# The package CI installs the locked standalone project. The legacy hub job
# deliberately does not install its Mongo driver or test backend.
collect_ignore_glob = ["test_*.py"] if find_spec("research_library_service") is None else []
