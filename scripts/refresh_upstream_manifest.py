"""Write tests/upstream_manifest.json: the fingerprint of the Microsoft-provided source at a pinned upstream commit.

The fork rule is that Microsoft's modules are never edited in place. A change goes into a duplicated module in
``agent_learning_ext`` so that merging ``upstream/main`` never clashes with code we wrote. ``tests/test_upstream_untouched.py``
enforces it by comparing every Microsoft source file with this manifest.

    uv run python scripts/refresh_upstream_manifest.py --init-known-edits   first time: record today's edits as debt
    uv run python scripts/refresh_upstream_manifest.py                      after a sync: move the pin, keep the debt list

Hashes ignore line endings, because git stores LF and a Windows working tree has CRLF. The ``known_edited`` list is debt:
it may only shrink. Never add a path to it by hand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "upstream_manifest.json"
PREFIX = "src/agent_learning/"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--pin", default="upstream/main", help="upstream revision to fingerprint (default: upstream/main)"
    )
    parser.add_argument(
        "--init-known-edits",
        action="store_true",
        help="record every file that differs from the pin as known debt",
    )
    args = parser.parse_args()

    pin = git("rev-parse", "--verify", args.pin).decode().strip()
    names = sorted(
        n
        for n in git("ls-tree", "-r", "--name-only", pin).decode().split()
        if n.startswith(PREFIX) and n.endswith(".py")
    )
    files = {n: fingerprint(git("show", f"{pin}:{n}")) for n in names}

    known: list[str] = []
    if args.init_known_edits:
        for n, digest in files.items():
            path = ROOT / n
            if not path.is_file() or fingerprint(path.read_bytes()) != digest:
                known.append(n)
    elif MANIFEST.is_file():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        known = [n for n in previous.get("known_edited", []) if n in files]

    manifest = {
        "_comment": (
            "Fingerprint of Microsoft-provided source at the pinned upstream commit. known_edited is debt from before the fork "
            "rule was written down: Microsoft files that were edited in place. It may only shrink. Restore a file from the pin, "
            "move the change into agent_learning_ext, then delete the path here. Never add to it."
        ),
        "pin": pin,
        "pin_ref": args.pin,
        "files": files,
        "known_edited": sorted(known),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"pin {pin[:10]}  files {len(files)}  known_edited {len(known)}  -> {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
