#!/usr/bin/env python3
"""gr86-revb-jlcpcb entry point using the baseline custody bridge."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
_SPEC = importlib.util.spec_from_file_location('gr86_assurance_custody', HERE / 'custody.py')
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)
_API = _CORE.bind(HERE, REPO, 'gr86-revb-jlcpcb')
Blocked = _API.Blocked
ROLES = _API.ROLES
load = _API.load
digest = _API.digest
write = _API.write
relative = _API.relative
inside = _API.inside
disjoint = _API.disjoint
new_dir = _API.new_dir
git = _API.git
catalog = _API.catalog
source_state = _API.source_state
framework = _API.framework
projection = _API.projection
hashes = _API.hashes
verify_capsule = _API.verify_capsule
verify_run_identity = _API.verify_run_identity
prepare = _API.prepare
command = _API.command
assess = _API.assess
mcp_config = _API.mcp_config
main = _API.main

if __name__ == '__main__':
    raise SystemExit(main())
