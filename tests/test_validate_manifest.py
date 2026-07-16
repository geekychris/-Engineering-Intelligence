from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_manifest)


class ManifestValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.build_dir = Path(self.temp_dir.name)
        (self.build_dir / "figures" / "mermaid").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_artifact(self, name: str, content: bytes) -> dict[str, object]:
        path = self.build_dir / name
        path.write_bytes(content)
        return {
            "name": name,
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }

    def write_manifest(self, *, mode: str, files: list[dict[str, object]], diagram_count: int = 0) -> None:
        manifest = {
            "schema_version": 1,
            "title": "Engineering Intelligence",
            "build_mode": mode,
            "publication_time": "2026-07-16T12:00:00+00:00",
            "source_date_epoch": 1784203200,
            "source_commit": "a" * 40,
            "files": files,
            "diagram_count": diagram_count,
        }
        (self.build_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_valid_html_manifest(self) -> None:
        artifact = self.write_artifact("engineering-intelligence.html", b"<html></html>")
        self.write_manifest(mode="html", files=[artifact])

        self.assertEqual(validate_manifest.validate(self.build_dir), 0)

    def test_valid_full_manifest_with_diagram(self) -> None:
        html = self.write_artifact("engineering-intelligence.html", b"<html></html>")
        pdf = self.write_artifact("engineering-intelligence.pdf", b"%PDF-test")
        (self.build_dir / "figures" / "mermaid" / "system.svg").write_text(
            "<svg/>", encoding="utf-8"
        )
        self.write_manifest(mode="validate", files=[html, pdf], diagram_count=1)

        self.assertEqual(validate_manifest.validate(self.build_dir), 0)

    def test_rejects_hash_mismatch(self) -> None:
        artifact = self.write_artifact("engineering-intelligence.html", b"original")
        artifact["sha256"] = "0" * 64
        self.write_manifest(mode="html", files=[artifact])

        self.assertEqual(validate_manifest.validate(self.build_dir), 1)

    def test_rejects_missing_expected_artifact(self) -> None:
        html = self.write_artifact("engineering-intelligence.html", b"<html></html>")
        self.write_manifest(mode="all", files=[html])

        self.assertEqual(validate_manifest.validate(self.build_dir), 1)

    def test_rejects_diagram_count_mismatch(self) -> None:
        artifact = self.write_artifact("engineering-intelligence.html", b"<html></html>")
        (self.build_dir / "figures" / "mermaid" / "one.svg").write_text(
            "<svg/>", encoding="utf-8"
        )
        self.write_manifest(mode="html", files=[artifact], diagram_count=0)

        self.assertEqual(validate_manifest.validate(self.build_dir), 1)

    def test_rejects_artifact_paths(self) -> None:
        nested = self.build_dir / "nested"
        nested.mkdir()
        content = b"unsafe"
        (nested / "engineering-intelligence.html").write_bytes(content)
        artifact = {
            "name": "nested/engineering-intelligence.html",
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }
        self.write_manifest(mode="html", files=[artifact])

        self.assertEqual(validate_manifest.validate(self.build_dir), 1)


if __name__ == "__main__":
    unittest.main()
