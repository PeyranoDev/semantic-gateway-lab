"""Create an exact public original/fixed case checkout without private GitHub access."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

CASE = Path(__file__).parents[1]/"case_studies/aoristo"

def materialize(out, variant):
    if variant not in ("original","fixed"):
        raise ValueError("unknown variant")
    target = Path(out).resolve()
    if target.exists():
        raise ValueError("refusing to overwrite a materialized case")
    shutil.copytree(CASE/"original", target, ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    if variant == "fixed":
        subprocess.run(["patch","--batch","--fuzz=0","-p1","-i",str(CASE/"fix.patch")],
                       cwd=target,check=True,capture_output=True,text=True)
    manifest = json.loads((CASE/"export-manifest.json").read_text())
    for path, entry in manifest["files"].items():
        expected = (manifest["patched_files"].get(path,entry["export_sha256"])
                    if variant == "fixed" else entry["export_sha256"])
        if hashlib.sha256((target/"backend/app"/path).read_bytes()).hexdigest() != expected:
            raise AssertionError("case source mismatch: "+path)
    return target

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant",choices=("original","fixed"),required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    print(materialize(args.out,args.variant))
