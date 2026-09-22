#!/usr/bin/env python3
"""Build the verified manifest for a Clink layout release."""
import hashlib
import json
import os
import pathlib

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
(root / "manifest.json").write_text(json.dumps({"version": version, "layouts": layouts}, indent=2) + "\n")
print(f"{len(layouts)} layouts · {version}")
