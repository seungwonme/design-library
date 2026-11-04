"""Design-book boundary checks against the real CLI and built artifacts."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesignBookTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture", "--allow-empty"], check=True)
        self.call("note", "sample", "--title", "A useful reference", "--source", "https://example.org/reference", "--platform", "web", "--category", "guideline")
        self.path = self.repo / "references/sample/reference.json"

    def call(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/reference-ui.py"), "--workspace", str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return json.loads(result.stdout or result.stderr)

    def save(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def ready(self):
        data = json.loads(self.path.read_text())
        data.update(status="ready", summary="A source-based study.")
        data["sources"][0].update(access="read", method="Read the official documentation.")
        data["evidence"] = [{"kind": "observed", "source_id": "source-1", "locator": "Introduction", "finding": "A documented pattern."}]
        data["assessment"] = {"why": "Clarifies an interaction.", "use_when": ["A relevant workflow"], "avoid_when": ["An unrelated context"], "takeaways": ["Preserve intent"]}
        data["details"] = [{"label": "Scope", "value": "Documentation only"}]
        data["verification"].update(level="source-read", checked_at="2026-01-01", scope="Read; not executed.")
        data["publication"].update(review="approved", rights="cleared", notes="Original commentary only.")
        self.save(data)
        return data

    def test_draft_has_no_fabricated_tokens_or_preview_and_cannot_be_ready(self):
        self.assertEqual(self.call("catalog")["items"], [])
        self.assertEqual(len(self.call("catalog", "--include-drafts")["items"]), 1)
        self.assertFalse((self.path.parent / "tokens.json").exists())
        self.call("validate", "sample", "--ready", ok=False)

    def test_book_build_generates_safe_readable_pages_and_no_token_link(self):
        data = self.ready()
        data["title"] = '</script><script>alert("fixture")</script>'
        data["summary"] = "{{CONTENT}} is plain text."
        self.save(data)
        self.call("build", "--output", str(self.repo / "site"))
        page = (self.repo / "site/references/sample/index.html").read_text()
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn('<script>alert(', page)
        self.assertIn("{{CONTENT}} is plain text.", page)
        item = self.call("catalog", "--public")["items"][0]
        self.assertEqual(item["tokens"], "")
        self.assertEqual(item["verification"], "source-read")

    def test_unsafe_source_and_unread_evidence_are_rejected(self):
        data = self.ready()
        data["sources"][0]["location"] = "javascript:alert(1)"
        self.save(data)
        self.call("validate", "sample", ok=False)
        data["sources"][0].update(location="https://example.org/", access="blocked")
        self.save(data)
        self.call("validate", "sample", ok=False)

    def test_hands_on_needs_evidence_and_flow_needs_recovery(self):
        data = self.ready()
        data["verification"]["level"] = "hands-on"
        self.save(data)
        self.call("validate", "sample", ok=False)
        data["verification"]["level"] = "source-read"
        data["category"] = "flow"
        self.save(data)
        self.call("validate", "sample", ok=False)

    def test_publication_rejects_unlisted_evidence_and_generated_preview(self):
        data = self.ready()
        (self.path.parent / "check.md").write_text("Synthetic test evidence.")
        data["verification"].update(level="hands-on", evidence=["check.md"])
        self.save(data)
        self.call("build", "--output", str(self.repo / "unlisted"), ok=False)
        data["publication"]["files"] += ["check.md", "index.html"]
        self.save(data)
        self.call("build", "--output", str(self.repo / "generated"), ok=False)

    def test_bundle_plan_does_not_write_and_default_branch_is_protected(self):
        self.assertFalse(self.call("bundle")["applied"])
        self.assertFalse((self.repo / ".reference-ui").exists())
        self.call("bundle", "--apply", ok=False)

    def test_note_creation_preserves_existing_record(self):
        before = self.path.read_bytes()
        self.call("note", "sample", "--title", "Overwrite", "--source", "https://example.org/", "--platform", "web", "--category", "library", ok=False)
        self.assertEqual(self.path.read_bytes(), before)

    def test_source_shape_errors_are_actionable_before_rendering(self):
        data = self.ready()
        for key in ("title", "method"):
            malformed = json.loads(json.dumps(data))
            malformed["sources"][0][key] = 42
            self.save(malformed)
            result = self.call("validate", "sample", ok=False)
            self.assertIn("source", result["error"].lower())

    def test_collect_saves_to_inbox_without_assessment(self):
        result = self.call("collect", "bookmark", "--source", "https://example.org/icons")
        self.assertTrue(result["created"])
        data = json.loads((self.repo / "references/bookmark/reference.json").read_text())
        self.assertEqual(data["category"], "inbox")
        self.assertEqual(data["note"], "")
        self.assertNotIn("assessment", data)
        self.assertNotIn("verification", data)
        self.assertEqual(self.call("catalog")["items"][0]["record_type"], "bookmark")
        self.assertEqual(self.call("catalog", "--public")["items"], [])

    def test_collect_reuses_source_without_overwriting_saved_notes(self):
        self.call("collect", "bookmark", "--source", "https://example.org/icons", "--note", "Keep my note", "--category", "asset")
        saved = self.repo / "references/bookmark/reference.json"
        before = saved.read_bytes()
        result = self.call("collect", "different-id", "--source", "https://example.org/icons", "--note", "Overwrite")
        self.assertFalse(result["created"])
        self.assertEqual(result["id"], "bookmark")
        self.assertEqual(saved.read_bytes(), before)
        self.assertFalse((self.repo / "references/different-id").exists())

    def test_collect_rejects_credentials_before_writing(self):
        self.call("collect", "bad-url", "--source", "https://person:synthetic@example.org/", ok=False)
        self.assertFalse((self.repo / "references/bad-url").exists())

    def test_local_preview_is_ignored_and_excluded_from_public_build(self):
        import base64
        image = self.repo / "fixture.png"
        image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII="))
        self.call("collect", "bookmark", "--source", "https://example.org/icons", "--image", str(image))
        repeated = self.call("collect", "bookmark", "--source", "https://example.org/icons", "--image", str(image))
        self.assertFalse(repeated["created"])
        another = self.repo / "different.jpg"
        another.write_bytes(b"Different synthetic image")
        self.call("collect", "bookmark", "--source", "https://example.org/icons", "--image", str(another), ok=False)
        self.assertFalse((self.repo / ".reference-previews/bookmark.jpg").exists())
        path = self.repo / "references/bookmark/reference.json"
        data = json.loads(path.read_text())
        data["publication"].update(review="approved", rights="cleared", notes="Original link and note only.")
        path.write_text(json.dumps(data))
        ignored = subprocess.run(["git", "check-ignore", ".reference-previews/bookmark.png"], cwd=self.repo, capture_output=True)
        self.assertEqual(ignored.returncode, 0)
        self.call("build", "--drafts", "--output", str(self.repo / "local"))
        self.assertEqual((self.repo / "local/previews/bookmark.png").read_bytes(), image.read_bytes())
        self.assertIn("previews/bookmark.png", (self.repo / "local/references/bookmark/index.html").read_text())
        self.call("build", "--output", str(self.repo / "public"))
        self.assertFalse((self.repo / "public/previews").exists())
        self.assertNotIn("previews/bookmark.png", (self.repo / "public/references/bookmark/index.html").read_text())

    def test_image_only_record_stays_local(self):
        import base64
        image = self.repo / "drawing.png"
        image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII="))
        self.call("collect", "drawing", "--image", str(image))
        record = self.repo / "references/drawing/reference.json"
        self.assertEqual(json.loads(record.read_text())["url"], "")
        self.call("build", "--drafts", "--output", str(self.repo / "image-view"))
        page = (self.repo / "image-view/references/drawing/index.html").read_text()
        self.assertIn("이미지 열기", page)
        self.assertIn("../../previews/drawing.png", page)
        self.call("validate", "drawing", "--public", ok=False)


if __name__ == "__main__":
    unittest.main()
