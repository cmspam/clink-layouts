#!/usr/bin/env python3
"""Build the verified manifest for a Clink layout release."""
import hashlib
import json
import os
import pathlib

# BEGIN repository platform policy (Tools/sync_repository_platforms.py)
def apply_platforms(root, manifest):
    """Annotate every pack; absent policy preserves legacy cross-platform packs."""
    path = root / "platforms.json"
    policy = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(policy, dict) or set(policy) - {"default", "overrides"}:
        raise ValueError("platforms.json must contain default and overrides only")
    default = policy.get("default", "both")
    overrides = policy.get("overrides", {})
    allowed = ("ios", "android", "both")
    if default not in allowed or not isinstance(overrides, dict):
        raise ValueError("Invalid repository platform policy")
    if any(value not in allowed for value in overrides.values()):
        raise ValueError("Platforms must be ios, android or both")
    entries = [entry for key, value in manifest.items() if isinstance(value, list)
               for entry in value]
    identifiers = {entry.get("id", entry.get("code", entry.get("locale"))) for entry in entries}
    if set(overrides) - identifiers:
        raise ValueError("Platform overrides name missing packs: " + str(sorted(set(overrides) - identifiers)))
    for entry in entries:
        identifier = entry.get("id", entry.get("code", entry.get("locale")))
        entry["platform"] = overrides.get(identifier, default)
    return manifest
# END repository platform policy


root = pathlib.Path(__file__).resolve().parents[1]
repository = os.environ.get("GITHUB_REPOSITORY", "anti-ltd/clink-layouts")
files = [(path, path.read_bytes())
         for path in sorted((root / "Layouts").glob("*.clinklayout"))
         if not path.name.startswith(".")]

# Each distinct set of bytes gets a permanent release URL. A cached manifest
# must never point at a newer file with a different checksum: a client that
# read the catalog before a release still installs the bytes it was promised.
# Hashing the layouts rather than the commit also means an unrelated push no
# longer offers every installed layout a pointless update.
identity = json.dumps([(path.name, hashlib.sha256(raw).hexdigest()) for path, raw in files],
                      separators=(",", ":"))
version = "layouts-" + hashlib.sha256(identity.encode()).hexdigest()

layouts = []
for path, raw in files:
    layout = json.loads(raw)
    layouts.append({
        "id": path.name.removesuffix(".clinklayout"),
        "name": layout["name"],
        "version": version,
        "asset": {
            "path": path.name,
            "url": f"https://github.com/{repository}/releases/download/{version}/{path.name}",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "byteCount": len(raw),
        },
    })
(root / "manifest.json").write_text(json.dumps(apply_platforms(root, {"version": version, "layouts": layouts}), indent=2) + "\n")
print(f"{len(layouts)} layouts · {version}")
