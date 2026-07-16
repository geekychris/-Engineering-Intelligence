from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_sources.py"
SPEC = importlib.util.spec_from_file_location("validate_sources", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_sources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_sources)


class SourceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "chapters").mkdir()
        (self.root / "figures" / "mermaid").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_chapter_pair(
        self,
        number: str = "01",
        stem: str = "introduction",
        *,
        notes_stem: str | None = None,
    ) -> tuple[str, str]:
        chapter_name = f"{number}-{stem}.adoc"
        notes_name = f"{number}-{notes_stem or stem}-source-notes.adoc"
        (self.root / "chapters" / chapter_name).write_text(
            "= Chapter\n\nChapter content.\n", encoding="utf-8"
        )
        (self.root / "chapters" / notes_name).write_text(
            "= Source Notes\n\nSource notes.\n", encoding="utf-8"
        )
        return chapter_name, notes_name

    def write_book(self, includes: list[tuple[str, int]]) -> None:
        lines = ["= Test Book", ""]
        for filename, level in includes:
            lines.append(
                f"include::chapters/{filename}[leveloffset=+{level}]"
            )
            lines.append("")
        (self.root / "book.adoc").write_text("\n".join(lines), encoding="utf-8")

    def test_valid_chapter_and_source_notes_pair(self) -> None:
        chapter, notes = self.write_chapter_pair()
        self.write_book([(chapter, 1), (notes, 2)])

        self.assertEqual(validate_sources.validate(self.root), 0)

    def test_rejects_missing_source_notes(self) -> None:
        chapter = "01-introduction.adoc"
        (self.root / "chapters" / chapter).write_text(
            "= Chapter\n", encoding="utf-8"
        )
        self.write_book([(chapter, 1)])

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_orphan_source_notes(self) -> None:
        notes = "01-introduction-source-notes.adoc"
        (self.root / "chapters" / notes).write_text(
            "= Source Notes\n", encoding="utf-8"
        )
        self.write_book([(notes, 2)])

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_source_notes_with_mismatched_stem(self) -> None:
        chapter, notes = self.write_chapter_pair(notes_stem="wrong-name")
        self.write_book([(chapter, 1), (notes, 2)])

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_source_notes_before_chapter(self) -> None:
        chapter, notes = self.write_chapter_pair()
        self.write_book([(notes, 2), (chapter, 1)])

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_wrong_level_offsets(self) -> None:
        chapter, notes = self.write_chapter_pair()
        self.write_book([(chapter, 2), (notes, 1)])

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_missing_included_file(self) -> None:
        chapter, notes = self.write_chapter_pair()
        self.write_book(
            [(chapter, 1), (notes, 2), ("02-missing.adoc", 1)]
        )

        self.assertEqual(validate_sources.validate(self.root), 1)

    def test_rejects_unresolved_citation_anchor(self) -> None:
        chapter, notes = self.write_chapter_pair()
        (self.root / "chapters" / chapter).write_text(
            "= Chapter\n\nSee <<missing2026>>.\n", encoding="utf-8"
        )
        self.write_book([(chapter, 1), (notes, 2)])

        self.assertEqual(validate_sources.validate(self.root), 1)


if __name__ == "__main__":
    unittest.main()
