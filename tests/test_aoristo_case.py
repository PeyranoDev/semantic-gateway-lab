"""Portable checks of real-source provenance and reproducible patch application."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.materialize_aoristo import CASE, materialize
from integrations.aoristo_case.provenance import verify_source

class PublicBackendCaseTests(unittest.TestCase):
    def test_original_source_matches_export_manifest(self):
        result=verify_source(CASE/"original","original")
        self.assertEqual(81,result["checked_files"])

    def test_verbatim_public_source_fingerprint(self):
        manifest=json.loads((CASE/"export-manifest.json").read_text())
        pairs={path:entry["export_sha256"] for path,entry in manifest["files"].items() if entry["status"]=="verbatim"}
        self.assertEqual(manifest["verbatim_export_fingerprint"],hashlib.sha256(json.dumps(pairs,sort_keys=True).encode()).hexdigest())

    def test_fixed_source_materializes_without_private_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            fixed=materialize(Path(folder)/"fixed","fixed")
            self.assertEqual(81,verify_source(fixed,"fixed")["checked_files"])
            manifest=json.loads((CASE/"export-manifest.json").read_text())
            changed=[p for p in manifest["files"] if
                (fixed/"backend/app"/p).read_bytes() != (CASE/"original/backend/app"/p).read_bytes()]
            self.assertEqual(set(manifest["patched_files"]),set(changed))

    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source=materialize(Path(folder)/"original","original")
            (source/"backend/app/application/use_cases/sale.py").write_text("tampered\n")
            with self.assertRaises(ValueError):verify_source(source,"original")

    def test_materialization_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):materialize(folder,"fixed")

    def test_export_preserves_real_entity_constructor(self):
        import runpy
        from uuid import UUID
        entities=runpy.run_path(str(CASE/"original/backend/app/domain/entities/redvecina.py"))
        invitation=entities["Invitation"](id=UUID(int=1),unit_id=UUID(int=2),token="public-test")
        self.assertEqual(0,invitation.current_uses)
        self.assertEqual(UUID(int=2),invitation.unit_id)

if __name__=="__main__":unittest.main()
