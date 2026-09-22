"""Download the pinned ALCE source and verify its exact bytes."""
import hashlib
from pathlib import Path
from urllib.request import urlopen
from citation_audit import SOURCE_URL, SOURCE_SHA256

if __name__ == "__main__":
    payload = urlopen(SOURCE_URL, timeout=60).read()
    if hashlib.sha256(payload).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Source checksum mismatch; refusing to save")
    target = Path("data/human_eval_citations_completed.json")
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(payload)
    print(f"Verified {len(payload):,} bytes: {target}")
