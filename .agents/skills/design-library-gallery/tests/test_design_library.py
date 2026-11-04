"""Isolated behavioral checks; evidence fixtures do not assert visual quality."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/design-library.py"


class DesignLibraryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="design-library-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "gallery"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.config = self.base / "settings/config.json"
        self.call("config", "init", "--workspace", str(self.repo))

    def call(self, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), "--config", str(self.config), *args], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return json.loads(result.stdout if result.stdout else result.stderr)

    def create(self):
        self.call("new", "sample-glass", "--title", "Sample glass", "--source", "https://example.org/ui", "--platform", "desktop")
        return self.repo / "references/sample-glass"

    def save(self, root, name, value):
        (root / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def ready(self):
        root = self.create()
        self.save(root, "tokens.json", {"space": {"$type": "dimension", "base": {"$value": {"value": 8, "unit": "px"}}, "gap": {"$value": "{space.base}"}}})
        (root / "DESIGN.md").write_text("# Synthetic fixture\nUse space.gap for the gap. This record only tests the validator.\n", encoding="utf-8")
        (root / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Fixture</title><p>Synthetic fixture</p>', encoding="utf-8")
        (root / "verification.md").write_text("Synthetic record used only to exercise file validation, not actual visual QA.\n", encoding="utf-8")
        meta = json.loads((root / "reference.json").read_text())
        meta["sources"][0]["method"] = "synthetic fixture"
        meta["evidence"] = [{"kind": "proposed", "source_id": "source-1", "locator": "fixture", "finding": "Synthetic spacing rule"}]
        meta["prototype"] = {"stack": "HTML", "reason": "Fixture", "run": "Open index.html"}
        for check in meta["verification"].values():
            check.update(status="pass", evidence=["verification.md"])
        self.save(root, "reference.json", meta)
        return root, meta

    def test_config_legacy_fallback_preserves_settings_and_new_config_wins(self):
        api, _ = self.bundle_modules()
        config_root = self.base / "xdg"
        legacy = config_root / "reference-ui/config.json"
        legacy.parent.mkdir(parents=True)
        legacy.write_bytes(self.config.read_bytes())
        before = legacy.read_bytes()
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(config_root)}):
            self.assertEqual(api.config_path(None), legacy)
            self.assertEqual(api.normalize_config(api.load_json(api.config_path(None)))["workspace_path"], str(self.repo.resolve()))
            current = config_root / "design-library/config.json"
            current.parent.mkdir()
            current.write_text("invalid new config")
            self.assertEqual(api.config_path(None), current)
            self.assertEqual(api.config_path(str(self.config)), self.config)
        self.assertEqual(legacy.read_bytes(), before)
        current.unlink()
        legacy.write_text("invalid legacy config")
        import os
        env = dict(os.environ, XDG_CONFIG_HOME=str(config_root))
        result = subprocess.run([sys.executable, str(SCRIPT), "doctor"], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid JSON", result.stderr)
        self.assertFalse(current.exists())

    def legacy_bundle(self):
        import hashlib
        api, gallery = self.bundle_modules()
        gallery.install_bundle(self.repo, "main", api, project_skill=True)
        manifest_path = self.repo / ".design-library/bundle.json"
        manifest = json.loads(manifest_path.read_text())
        old_files = {}
        for name in manifest["files"]:
            old = name.replace("design-library", "reference-ui").replace("test_design_library.py", "test_reference_ui.py")
            source = self.repo / name
            payload = source.read_bytes().replace(b"design-library", b"reference-ui")
            if source != self.repo / old:
                source.unlink()
            target = self.repo / old
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            old_files[old] = hashlib.sha256(payload).hexdigest()
        manifest_path.unlink()
        legacy = self.repo / ".reference-ui/bundle.json"
        legacy.write_text(json.dumps({"project_skill": "reference-ui-gallery", "files": old_files}))
        return api, gallery, legacy

    def test_legacy_bundle_migrates_project_skill_preserving_unmanaged_files(self):
        api, gallery, legacy = self.legacy_bundle()
        extra = self.repo / ".reference-ui/user-notes.txt"
        extra.write_text("Keep me")
        managed, removed = gallery.install_bundle(self.repo, "main", api)
        self.assertFalse(legacy.exists())
        self.assertEqual(extra.read_text(), "Keep me")
        self.assertIn(".reference-ui/bundle.json", removed)
        self.assertIn(".agents/skills/design-library-gallery/SKILL.md", managed)
        result = subprocess.run([sys.executable, str(self.repo / "scripts/gallery.py"), "doctor"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(gallery.install_bundle(self.repo, "main", api)[1], [])

    def test_legacy_manifest_survives_intermediate_write_failure(self):
        api, gallery, legacy = self.legacy_bundle()
        before = legacy.read_bytes()
        original_write = Path.write_bytes
        written = []

        def fail_second_write(path, data):
            if written:
                raise OSError("Synthetic intermediate migration write failure")
            result = original_write(path, data)
            written.append(path)
            return result

        with patch.object(Path, "write_bytes", fail_second_write):
            with self.assertRaisesRegex(OSError, "intermediate migration"):
                gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].is_file())
        self.assertEqual(legacy.read_bytes(), before)
        self.assertFalse((self.repo / ".design-library/bundle.json").exists())

    def test_legacy_bundle_conflicts_and_edits_fail_without_writes(self):
        api, gallery, legacy = self.legacy_bundle()
        conflict = self.repo / ".design-library/assets/gallery.html"
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_text("Unmanaged replacement")
        before = self.bundle_snapshot()
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(self.bundle_snapshot(), before)
        conflict.unlink()
        edited = self.repo / ".reference-ui/assets/gallery.html"
        edited.write_text("Edited legacy content")
        before = self.bundle_snapshot()
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(self.bundle_snapshot(), before)

    def test_two_bundle_manifests_refuse_ambiguous_ownership(self):
        api, gallery, legacy = self.legacy_bundle()
        current = self.repo / ".design-library/bundle.json"
        current.write_text('{"files": {}}')
        before = self.bundle_snapshot()
        with self.assertRaisesRegex(api.UserError, "Both legacy"):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(self.bundle_snapshot(), before)

    def test_pending_legacy_workflow_remains_resumable(self):
        _, gallery = self.bundle_modules()
        for name in ("UI reference pages", "Design Library pages"):
            run = {"workflowName": name, "headSha": "abc", "status": "completed", "conclusion": "success", "url": "https://example.org/run"}
            result = subprocess.CompletedProcess([], 0, stdout=json.dumps([run]))
            with patch.object(gallery, "command", return_value=result):
                self.assertEqual(gallery.wait_workflow("example/repo", "abc", "push", 1), run)

    def test_config_is_idempotent_and_change_is_explicit(self):
        before = self.config.read_bytes()
        self.assertFalse(self.call("config", "init", "--workspace", str(self.repo))["changed"])
        self.call("config", "init", "--workspace", str(self.base / "other"), ok=False)
        self.assertEqual(self.config.read_bytes(), before)
        self.call("config", "set", "--workspace", str(self.base / "other"))
        self.assertFalse((self.base / "other").exists())
        self.assertIn("does not exist", self.call("doctor", ok=False)["error"])

    def test_bad_json_does_not_fall_back_or_write(self):
        self.config.write_text('{"workspace_path":', encoding="utf-8")
        before = self.config.read_bytes()
        self.assertIn("Invalid JSON", self.call("doctor", ok=False)["error"])
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.repo / "references").exists())

    def test_config_lock_is_not_silently_removed(self):
        lock = self.config.with_name("config.json.lock")
        lock.write_text("owned by another writer")
        self.call("config", "set", "--remote-name", "upstream", ok=False)
        self.assertTrue(lock.exists())

    def test_remote_identity_and_mismatch_do_not_modify_git(self):
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "git@example.org:team/gallery.git"], check=True)
        self.call("config", "set", "--bootstrap-url", "https://example.org/team/gallery.git")
        self.assertEqual(self.call("doctor")["bootstrap_comparison"], "match")
        self.call("config", "set", "--bootstrap-url", "https://example.org/team/another.git")
        self.assertEqual(self.call("doctor", ok=False)["bootstrap_comparison"], "mismatch-or-unresolved")
        self.call("new", "wrong", "--title", "Wrong", "--source", "source", "--platform", "web", ok=False)
        remote = subprocess.check_output(["git", "-C", str(self.repo), "remote", "get-url", "origin"], text=True)
        self.assertEqual(remote.strip(), "git@example.org:team/gallery.git")
        self.assertFalse((self.repo / "references/wrong").exists())

    def test_credentials_are_rejected_without_echo(self):
        output = self.call("config", "set", "--bootstrap-url", "https://user:example-password@example.org/team/gallery", ok=False)
        self.assertNotIn("example-password", json.dumps(output))
        self.assertEqual(json.loads(self.config.read_text())["bootstrap_url"], "")

    def test_new_preserves_existing_item_and_rejects_traversal(self):
        root = self.create()
        original = (root / "reference.json").read_bytes()
        self.call("new", "sample-glass", "--title", "Overwrite", "--source", "source", "--platform", "web", ok=False)
        self.assertEqual((root / "reference.json").read_bytes(), original)
        self.call("new", "../escape", "--title", "Escape", "--source", "source", "--platform", "web", ok=False)
        self.assertFalse((self.repo / "escape").exists())

    def test_source_credentials_rejected_before_creating_entry(self):
        for source in ["https://demo:synthetic-secret@example.org/ui", "https://example.org/ui?access_token=synthetic-secret", "https://example.org/ui#access_token=synthetic-secret"]:
            output = self.call("new", "credential-source", "--title", "Fixture", "--source", source, "--platform", "web", ok=False)
            self.assertNotIn("synthetic-secret", json.dumps(output))
            self.assertFalse((self.repo / "references/credential-source").exists())

    def test_existing_source_credentials_block_public_validation(self):
        root, meta = self.ready()
        meta["sources"][0]["location"] = "https://demo:synthetic-secret@example.org/ui"
        self.save(root, "reference.json", meta)
        output = self.call("validate", "sample-glass", "--public", ok=False)
        self.assertIn("credentials", output["error"])
        self.assertNotIn("synthetic-secret", json.dumps(output))

    def test_draft_is_not_ready_and_not_in_default_catalog(self):
        self.create()
        self.call("validate", "sample-glass")
        self.call("validate", "sample-glass", "--ready", ok=False)
        self.assertEqual(self.call("catalog")["items"], [])
        self.assertEqual(len(self.call("catalog", "--include-drafts")["items"]), 1)

    def test_ready_and_public_are_separate_gates(self):
        root, meta = self.ready()
        self.assertEqual(self.call("validate", "sample-glass", "--ready")["tokens"], 2)
        self.call("validate", "sample-glass", "--public", ok=False)
        meta["status"] = "ready"
        self.save(root, "reference.json", meta)
        self.assertEqual(len(self.call("catalog")["items"]), 1)
        self.assertEqual(self.call("catalog", "--public")["items"], [])
        meta["publication"] = {"review": "approved", "rights": "cleared", "notes": "Synthetic authored fixture"}
        self.save(root, "reference.json", meta)
        item = self.call("catalog", "--public")["items"][0]
        self.assertEqual(item["design"], "references/sample-glass/DESIGN.md")
        self.assertNotIn("sources", item)
        self.call("catalog", "--public", "--include-drafts", ok=False)

    def test_broken_alias_and_cycle_fail_before_valid_graph(self):
        root, _ = self.ready()
        self.save(root, "tokens.json", {"a": {"$type": "number", "$value": "{missing}"}})
        self.assertIn("Missing token", self.call("validate", "sample-glass", ok=False)["error"])
        self.save(root, "tokens.json", {"a": {"$value": "{b}"}, "b": {"$value": "{a}"}})
        self.assertIn("Circular", self.call("validate", "sample-glass", ok=False)["error"])
        self.save(root, "tokens.json", {"a": {"$type": "number", "$value": 1}, "b": {"$value": "{a}"}})
        self.call("validate", "sample-glass", "--ready")

    def test_ready_requires_actual_evidence_file(self):
        root, meta = self.ready()
        meta["verification"]["new_screen"]["evidence"] = ["missing.md"]
        self.save(root, "reference.json", meta)
        self.call("validate", "sample-glass", "--ready", ok=False)
        meta["verification"]["new_screen"] = {"status": "not-applicable", "evidence": [], "reason": "Not tested"}
        self.save(root, "reference.json", meta)
        self.call("validate", "sample-glass", "--ready", ok=False)

    def test_local_and_symlink_preview_escape_rejected(self):
        root, meta = self.ready()
        outside = self.base / "private.html"
        outside.write_text("Private fixture")
        meta["preview"] = "../../private.html"
        self.save(root, "reference.json", meta)
        self.call("validate", "sample-glass", ok=False)
        (root / "linked.html").symlink_to(outside)
        meta["preview"] = "linked.html"
        self.save(root, "reference.json", meta)
        self.call("validate", "sample-glass", ok=False)

    def test_references_symlink_rejected_before_write(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.repo / "references").symlink_to(outside, target_is_directory=True)
        self.call("new", "escape", "--title", "Escape", "--source", "source", "--platform", "web", ok=False)
        self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_field_types_return_actionable_json(self):
        root, meta = self.ready()
        meta["platforms"] = [{}]
        self.save(root, "reference.json", meta)
        self.assertIn("platforms", self.call("validate", "sample-glass", ok=False)["error"])
        meta["platforms"] = ["web"]
        meta["verification"]["visual"]["status"] = []
        self.save(root, "reference.json", meta)
        self.assertIn("visual", self.call("validate", "sample-glass", ok=False)["error"])

    def public_ready(self):
        root, meta = self.ready()
        meta["status"] = "ready"
        meta["publication"] = {"review": "approved", "rights": "cleared", "notes": "Synthetic authored fixture", "files": ["DESIGN.md", "tokens.json", "reference.json", "index.html", "verification.md"]}
        self.save(root, "reference.json", meta)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.org", "commit", "--allow-empty", "-qm", "test fixture"], check=True)
        return root, meta

    def test_build_exports_only_reviewed_files_and_rejects_stale_output(self):
        root, meta = self.public_ready()
        (root / "private-notes.txt").write_text("Private fixture, not approved for publication")
        output = self.base / "site"
        self.assertEqual(self.call("build", "--output", str(output))["entries"], ["sample-glass"])
        self.assertFalse((output / "references/sample-glass/private-notes.txt").exists())
        before = (output / "build.json").read_bytes()
        self.call("build", "--output", str(output), ok=False)
        self.assertEqual((output / "build.json").read_bytes(), before)

    def test_repo_gallery_style_is_built_without_modifying_source(self):
        self.public_ready()
        style = self.repo / "gallery.css"
        content = ':root{--g-fg:#123456}\n'
        style.write_text(content)
        output = self.base / "styled"
        self.call("build", "--output", str(output))
        self.assertEqual((output / "gallery.css").read_text(), content)
        self.assertIn('href="gallery.css"', (output / "index.html").read_text())
        self.assertEqual(style.read_text(), content)
        self.assertIn("gallery.css", json.loads((output / "build.json").read_text())["files"])

    def test_gallery_style_rejects_private_paths_missing_assets_and_symlinks(self):
        self.public_ready()
        style = self.repo / "gallery.css"
        style.write_text('body{background:url(file:///private/example)}')
        self.call("build", "--output", str(self.base / "private"), ok=False)
        style.write_text('body{background:url(missing.jpg)}')
        self.call("build", "--output", str(self.base / "missing"), ok=False)
        style.unlink()
        outside = self.base / "external.css"
        outside.write_text('body{color:red}')
        style.symlink_to(outside)
        self.call("build", "--output", str(self.base / "symlink"), ok=False)

    def test_build_requires_explicit_public_file_list(self):
        root, meta = self.public_ready()
        del meta["publication"]["files"]
        self.save(root, "reference.json", meta)
        self.call("build", "--output", str(self.base / "site"), ok=False)
        self.assertFalse((self.base / "site").exists())

    def test_build_blocks_machine_paths_and_broken_links(self):
        root, meta = self.public_ready()
        (root / "DESIGN.md").write_text("Machine file:///private/example")
        self.call("build", "--output", str(self.base / "site"), ok=False)
        (root / "DESIGN.md").write_text("Synthetic design rules")
        (root / "index.html").write_text('<a href="missing.html">Missing</a>')
        self.call("build", "--output", str(self.base / "site"), ok=False)

    def test_build_escapes_catalog_data_and_generates_token_css(self):
        root, meta = self.public_ready()
        meta["title"] = '</script><img id="injected">'
        meta["prototype"]["token_css"] = "assets/tokens.css"
        self.save(root, "reference.json", meta)
        self.save(root, "tokens.json", {"space": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}, "$extensions": {"reference-ui": {"css_name": "--space"}}}})
        (root / "index.html").write_text('<link rel="stylesheet" href="assets/tokens.css"><p>Fixture</p>')
        output = self.base / "site"
        self.call("build", "--output", str(output))
        self.assertIn("--space:8px", (output / "references/sample-glass/assets/tokens.css").read_text())
        self.assertNotIn(meta["title"], (output / "index.html").read_text())

    def test_draft_preview_is_marked_and_forbidden_in_ci(self):
        root, meta = self.public_ready()
        meta["status"] = "draft"
        meta["verification"]["new_screen"] = {"status": "not-run", "evidence": [], "reason": ""}
        meta["publication"]["review"] = "pending"
        self.save(root, "reference.json", meta)
        self.call("build", "--output", str(self.base / "public"), ok=False)
        import os
        local_env = dict(os.environ)
        local_env.pop("GITHUB_ACTIONS", None)
        self.call("build", "--drafts", "--output", str(self.base / "draft"), env=local_env)
        self.assertTrue(json.loads((self.base / "draft/build.json").read_text())["drafts"])
        self.assertIn("DRAFT", (self.base / "draft/index.html").read_text())
        env = dict(os.environ, GITHUB_ACTIONS="true")
        result = subprocess.run([sys.executable, str(SCRIPT), "--config", str(self.config), "build", "--drafts", "--output", str(self.base / "ci")], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("local-only", result.stderr)
        self.assertFalse((self.base / "ci").exists())

    def test_publish_plan_does_not_mutate_or_contact_remote(self):
        root, _ = self.public_ready()
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.com/example/reference-fixture.git"], check=True)
        before = subprocess.check_output(["git", "-C", str(self.repo), "status", "--porcelain"])
        result = self.call("publish", str(root), "--merge")
        self.assertEqual(result["stage"], "plan")
        self.assertEqual(before, subprocess.check_output(["git", "-C", str(self.repo), "status", "--porcelain"]))
        self.assertFalse((self.repo / ".design-library").exists())

    def test_style_publish_plan_reads_only_explicit_css_without_mutating_checkout(self):
        root, _ = self.public_ready()
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.com/example/reference-fixture.git"], check=True)
        style = self.base / "theme.css"
        style.write_text(':root{--g-fg:#123456}')
        result = self.call("publish", str(root), "--gallery-style", str(style))
        self.assertEqual(result["gallery_style"], "gallery.css")
        self.assertFalse((self.repo / "gallery.css").exists())
        style.write_text('body{background:url(file:///private/example)}')
        self.call("publish", str(root), "--gallery-style", str(style), ok=False)

    def test_bundled_builder_runs_without_installed_skill_or_user_config(self):
        root, _ = self.public_ready()
        import importlib.util
        spec = importlib.util.spec_from_file_location("design_library_test_api", SCRIPT)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        gallery_spec = importlib.util.spec_from_file_location("design_library_test_gallery", ROOT / "scripts/gallery.py")
        gallery = importlib.util.module_from_spec(gallery_spec)
        gallery_spec.loader.exec_module(gallery)
        gallery.install_bundle(self.repo, "main", api)
        result = subprocess.run([sys.executable, str(self.repo / "scripts/gallery.py"), "build", "--output", str(self.base / "standalone")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.base / "standalone/build.json").exists())
        target = self.repo / ".design-library/assets/gallery.css"
        target.write_text("User-owned change")
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(target.read_text(), "User-owned change")

    def bundle_modules(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("project_bundle_api", SCRIPT)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        spec = importlib.util.spec_from_file_location("project_bundle_gallery", ROOT / "scripts/gallery.py")
        gallery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gallery)
        return api, gallery

    def bundle_fixture(self, label, project_skill=False):
        api, gallery = self.bundle_modules()
        worktree = self.base / label
        worktree.mkdir()
        api.SKILL_ROOT = self.base / (label + "-source")
        api.ASSETS = api.SKILL_ROOT / "assets"
        files = {
            "assets/kept.txt": b"Previous generated content\n",
            "assets/removed.txt": b"Retired generated content\n",
            "assets/missing.txt": b"Another retired file\n",
            "assets/pages.yml": b"branches: [DEFAULT_BRANCH]\n",
            "scripts/design-library.py.lock": b"Synthetic lock\n",
            "references/setup.md": b"Previous setup instructions\n",
        }
        for name, data in files.items():
            path = api.SKILL_ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        gallery.RUNTIME_FILES = ("assets/kept.txt", "assets/removed.txt", "assets/missing.txt")
        gallery.SKILL_FILES = ("references/setup.md",)
        gallery.install_bundle(worktree, "main", api, project_skill=project_skill)
        gallery.RUNTIME_FILES = ("assets/kept.txt",)
        (api.ASSETS / "kept.txt").write_bytes(b"Updated generated content\n")
        return api, gallery, worktree

    def bundle_snapshot(self):
        snapshot = {}
        for path in self.base.rglob("*"):
            if path.is_symlink():
                value = ("symlink", str(path.readlink()))
            elif path.is_file():
                value = ("file", path.read_bytes())
            else:
                value = ("other", path.stat().st_mode)
            snapshot[path.relative_to(self.base).as_posix()] = value
        return snapshot

    def test_bundle_removes_retired_files_and_keeps_unmanaged_files(self):
        api, gallery, worktree = self.bundle_fixture("retired")
        removed = ".design-library/assets/removed.txt"
        missing = ".design-library/assets/missing.txt"
        (worktree / missing).unlink()
        unmanaged = worktree / ".design-library/assets/user.txt"
        unmanaged.write_bytes(b"User-owned content\n")
        managed, retired = gallery.install_bundle(worktree, "release", api)
        self.assertFalse((worktree / removed).exists())
        self.assertFalse((worktree / missing).exists())
        self.assertEqual(unmanaged.read_bytes(), b"User-owned content\n")
        self.assertEqual((worktree / ".design-library/assets/kept.txt").read_bytes(), b"Updated generated content\n")
        manifest = json.loads((worktree / ".design-library/bundle.json").read_text())
        self.assertNotIn(removed, manifest["files"])
        self.assertNotIn(missing, manifest["files"])
        self.assertNotIn(unmanaged.relative_to(worktree).as_posix(), manifest["files"])
        self.assertIn(removed, retired)
        self.assertIn(missing, retired)
        self.assertIn("branches: [release]", (worktree / ".github/workflows/pages.yml").read_text())

    def test_bundle_modified_files_block_all_writes_and_retirements(self):
        for name in ("missing.txt", "kept.txt"):
            with self.subTest(name=name):
                api, gallery, worktree = self.bundle_fixture("modified-" + name)
                (worktree / ".design-library/assets" / name).write_bytes(b"User-owned edit\n")
                # Matching the new generator still does not authorize an edit to an old managed file.
                (api.ASSETS / name).write_bytes(b"User-owned edit\n")
                before = self.bundle_snapshot()
                with self.assertRaisesRegex(api.UserError, "edited outside"):
                    gallery.install_bundle(worktree, "release", api)
                self.assertEqual(self.bundle_snapshot(), before)

    def test_bundle_retired_unsafe_targets_fail_before_any_mutation(self):
        import os
        kinds = ("symlink", "dangling-symlink", "parent-symlink", "directory", "hard-link")
        if hasattr(os, "mkfifo"):
            kinds += ("fifo",)
        for kind in kinds:
            with self.subTest(kind=kind):
                api, gallery, worktree = self.bundle_fixture("unsafe-" + kind)
                target = worktree / ".design-library/assets/missing.txt"
                outside = api.SKILL_ROOT / "user.txt"
                outside.write_bytes(target.read_bytes())
                if kind == "parent-symlink":
                    moved = api.SKILL_ROOT / "old-assets"
                    target.parent.rename(moved)
                    target.parent.symlink_to(moved, target_is_directory=True)
                elif kind == "hard-link":
                    (api.SKILL_ROOT / "linked.txt").hardlink_to(target)
                else:
                    target.unlink()
                    if kind == "directory":
                        target.mkdir()
                        (target / "user.txt").write_bytes(b"User-owned directory\n")
                    elif kind == "fifo":
                        os.mkfifo(target)
                    else:
                        target.symlink_to(outside if kind == "symlink" else api.SKILL_ROOT / "absent")
                before = self.bundle_snapshot()
                with self.assertRaises(api.UserError):
                    gallery.install_bundle(worktree, "release", api)
                self.assertEqual(self.bundle_snapshot(), before)

    def test_bundle_invalid_manifest_paths_and_hashes_preserve_every_file(self):
        cases = ("traversal", "absolute", "empty", "dot", "alias", "backslash", "git", "manifest", "hash", "files")
        for kind in cases:
            with self.subTest(kind=kind):
                api, gallery, worktree = self.bundle_fixture("invalid-" + kind)
                outside = api.SKILL_ROOT / "user.txt"
                outside.write_bytes(b"User-owned content\n")
                manifest_path = worktree / ".design-library/bundle.json"
                manifest = json.loads(manifest_path.read_text())
                paths = {"traversal": "../" + outside.parent.name + "/user.txt", "absolute": str(outside),
                         "empty": "", "dot": ".", "alias": ".design-library//assets/removed.txt",
                         "backslash": ".design-library\\assets\\removed.txt", "git": ".git/config",
                         "manifest": ".design-library/bundle.json"}
                if kind == "files":
                    manifest["files"] = []
                elif kind == "hash":
                    manifest["files"][".design-library/assets/removed.txt"] = "not-a-hash"
                else:
                    manifest["files"][paths[kind]] = gallery.hashlib.sha256(outside.read_bytes()).hexdigest()
                manifest_path.write_text(api.dump_json(manifest))
                before = self.bundle_snapshot()
                with self.assertRaises(api.UserError):
                    gallery.install_bundle(worktree, "release", api)
                self.assertEqual(self.bundle_snapshot(), before)

    def test_bundle_new_target_conflicts_block_retirements(self):
        for kind in ("file", "parent"):
            with self.subTest(kind=kind):
                api, gallery, worktree = self.bundle_fixture("conflict-" + kind)
                relative = "assets/new.txt" if kind == "file" else "assets/new/child.txt"
                source = api.SKILL_ROOT / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(b"New generated file\n")
                gallery.RUNTIME_FILES += (relative,)
                target = worktree / ".design-library" / relative
                (target if kind == "file" else target.parent).write_bytes(b"User-owned content\n")
                before = self.bundle_snapshot()
                with self.assertRaises(api.UserError):
                    gallery.install_bundle(worktree, "release", api)
                self.assertEqual(self.bundle_snapshot(), before)

    def test_bundle_case_only_rename_removes_old_identity_before_writing(self):
        for emulate_case_insensitive in (False, True):
            with self.subTest(emulate_case_insensitive=emulate_case_insensitive):
                api, gallery, worktree = self.bundle_fixture("rename-" + str(emulate_case_insensitive), project_skill=True)
                old = gallery.PROJECT_SKILL_ROOT + "/references/setup.md"
                new = gallery.PROJECT_SKILL_ROOT + "/references/SETUP.md"
                source = api.SKILL_ROOT / "references/setup.md"
                source.rename(source.with_name("SETUP.md"))
                source.with_name("SETUP.md").write_bytes(b"Updated setup instructions\n")
                gallery.SKILL_FILES = ("references/SETUP.md",)
                lookup = gallery.managed_path
                write = Path.write_bytes

                def managed_path(root, name, module):
                    if emulate_case_insensitive and root == worktree and name == new:
                        return lookup(root, old, module)
                    return lookup(root, name, module)

                def write_bytes(path, data):
                    if path == worktree / new:
                        self.assertFalse((worktree / old).exists())
                    return write(path, data)

                with patch.object(gallery, "managed_path", side_effect=managed_path), patch.object(Path, "write_bytes", write_bytes):
                    managed, retired = gallery.install_bundle(worktree, "main", api, project_skill=True)
                self.assertEqual([path.name for path in (worktree / new).parent.iterdir()], ["SETUP.md"])
                self.assertEqual((worktree / new).read_bytes(), b"Updated setup instructions\n")
                manifest = json.loads((worktree / ".design-library/bundle.json").read_text())
                self.assertNotIn(old, manifest["files"])
                self.assertIn(new, manifest["files"])
                self.assertIn(old, retired)
                self.assertIn(new, managed)

    def test_bundle_case_only_rename_survives_case_insensitive_git_index(self):
        api, gallery, worktree = self.bundle_fixture("git-rename", project_skill=True)
        subprocess.run(["git", "init", "-q", str(worktree)], check=True)
        subprocess.run(["git", "-C", str(worktree), "config", "core.ignorecase", "true"], check=True)
        subprocess.run(["git", "-C", str(worktree), "add", "--", ".design-library", "scripts", ".github", ".agents"], check=True)
        old = gallery.PROJECT_SKILL_ROOT + "/references/setup.md"
        new = gallery.PROJECT_SKILL_ROOT + "/references/SETUP.md"
        source = api.SKILL_ROOT / "references/setup.md"
        source.rename(source.with_name("SETUP.md"))
        gallery.SKILL_FILES = ("references/SETUP.md",)
        managed, retired = gallery.install_bundle(worktree, "main", api, project_skill=True)
        gallery.stage_bundle(worktree, managed, retired)
        indexed = subprocess.check_output(["git", "-C", str(worktree), "ls-files", "-z"], text=True).split("\0")
        self.assertIn(new, indexed)
        self.assertNotIn(old, indexed)
        self.assertNotIn(".design-library/assets/removed.txt", indexed)
        self.assertEqual(subprocess.check_output(["git", "-C", str(worktree), "config", "core.ignorecase"], text=True).strip(), "true")

    def test_bundle_manifest_is_not_updated_when_writing_fails(self):
        api, gallery, worktree = self.bundle_fixture("write-failure")
        manifest_path = worktree / ".design-library/bundle.json"
        before = manifest_path.read_bytes()
        with patch.object(Path, "write_bytes", side_effect=OSError("Synthetic write failure")):
            with self.assertRaisesRegex(OSError, "Synthetic write failure"):
                gallery.install_bundle(worktree, "main", api)
        self.assertEqual(manifest_path.read_bytes(), before)

    def test_minimal_runtime_check_runs_tests_and_rejects_zero_run(self):
        self.public_ready()
        api, gallery = self.bundle_modules()
        gallery.install_bundle(self.repo, "main", api)
        runner = self.repo / "scripts/gallery.py"
        result = subprocess.run([sys.executable, str(runner), "check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["regressions"]["suite"], "token-and-book")
        self.assertGreater(report["regressions"]["tests"], 0)
        self.assertTrue(report["build"]["temporary_output_removed"])
        (self.repo / ".design-library/tests/test_token_contract.py").write_text("# Empty damaged test bundle\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(runner), "check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stderr, "zero tests|NO TESTS RAN")

    def test_exported_skill_and_bundle_share_release_version(self):
        api, gallery = self.bundle_modules()
        gallery.install_bundle(self.repo, "main", api, project_skill=True)
        manifest = json.loads((self.repo / ".design-library/bundle.json").read_text())
        skill = (self.repo / ".agents/skills/design-library-gallery/SKILL.md").read_text()
        declared = next(line.partition(":")[2].strip().strip('"') for line in skill.splitlines() if line.startswith("  version:"))
        self.assertEqual(manifest["version"], declared)

    def test_project_skill_bundle_runs_after_relocation_without_user_config(self):
        self.public_ready()
        api, gallery = self.bundle_modules()
        gallery.install_bundle(self.repo, "main", api, project_skill=True)
        skill = self.repo / ".agents/skills/design-library-gallery"
        self.assertIn("name: design-library-gallery\n", (skill / "SKILL.md").read_text())
        for relative in ("README.md", "references/extraction.md", "references/SETUP.md", "tests/test_design_library.py", "assets/config.example.json"):
            self.assertTrue((skill / relative).is_file(), relative)
        self.assertEqual(json.loads((skill / "assets/config.example.json").read_text())["workspace_path"], "")
        import shutil
        moved = self.base / "relocated"
        shutil.copytree(self.repo, moved)
        (moved / ".design-library/scripts").rename(self.base / "legacy-runtime")
        self.config.write_text("invalid user config")
        result = subprocess.run([sys.executable, str(moved / "scripts/gallery.py"), "--config", str(self.config), "build", "--output", str(self.base / "portable")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["entries"], ["sample-glass"])

    def test_project_skill_bundle_is_preserved_on_later_publications(self):
        self.public_ready()
        api, gallery = self.bundle_modules()
        gallery.install_bundle(self.repo, "main", api, project_skill=True)
        missing = self.repo / ".agents/skills/design-library-gallery/references/extraction.md"
        missing.unlink()
        managed, _ = gallery.install_bundle(self.repo, "main", api)
        self.assertTrue(missing.is_file())
        self.assertIn(".agents/skills/design-library-gallery/SKILL.md", managed)
        self.assertEqual(json.loads((self.repo / ".design-library/bundle.json").read_text())["project_skill"], "design-library-gallery")

    def test_project_skill_local_edits_and_symlinks_block_before_writes(self):
        self.public_ready()
        api, gallery = self.bundle_modules()
        outside = self.base / "outside"
        outside.mkdir()
        (self.repo / ".agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api, project_skill=True)
        self.assertFalse((self.repo / ".design-library").exists())
        self.assertEqual(list(outside.iterdir()), [])
        (self.repo / ".agents").unlink()
        gallery.install_bundle(self.repo, "main", api, project_skill=True)
        manifest = (self.repo / ".design-library/bundle.json").read_bytes()
        source = self.repo / ".agents/skills/design-library-gallery/references/SETUP.md"
        source.write_text("User-owned instructions")
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(source.read_text(), "User-owned instructions")
        self.assertEqual((self.repo / ".design-library/bundle.json").read_bytes(), manifest)

    def test_project_skill_plan_does_not_write_or_contact_remote(self):
        root, _ = self.public_ready()
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.com/example/reference-fixture.git"], check=True)
        result = self.call("publish", str(root), "--project-skill")
        self.assertEqual(result["project_skill"], "design-library-gallery")
        self.assertFalse((self.repo / ".agents").exists())

    def test_project_exception_keeps_global_installation_separate(self):
        api, _ = self.bundle_modules()
        api.SKILL_ROOT = (self.repo / "skills/shared/design-library").resolve()
        api.SKILL_ROOT.mkdir(parents=True)
        (api.SKILL_ROOT / "SKILL.md").write_text("Synthetic skill")
        data = api.normalize_config({"workspace_path": str(self.repo), "bootstrap_url": "", "remote_name": "origin"})
        with self.assertRaisesRegex(api.UserError, "separate"):
            api.workspace_info(data)

    def test_publish_rejects_fully_documented_draft(self):
        root, meta = self.public_ready()
        meta["status"] = "draft"
        self.save(root, "reference.json", meta)
        self.assertIn("status=ready", self.call("publish", str(root), ok=False)["error"])

    def test_bundle_rejects_manifest_and_parent_symlinks_without_writes(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("design_library_path_api", SCRIPT)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        spec = importlib.util.spec_from_file_location("design_library_path_gallery", ROOT / "scripts/gallery.py")
        gallery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gallery)
        outside = self.base / "outside"
        outside.mkdir()
        original = outside / "settings.json"
        original.write_text('{"keep": true}')
        bundle = self.repo / ".design-library"
        bundle.mkdir()
        (bundle / "bundle.json").symlink_to(original)
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertEqual(original.read_text(), '{"keep": true}')
        (bundle / "bundle.json").unlink()
        (self.repo / "scripts").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(api.UserError):
            gallery.install_bundle(self.repo, "main", api)
        self.assertFalse((outside / "gallery.py").exists())
        (self.repo / "references").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(api.UserError):
            gallery.managed_path(self.repo, "references/new-entry", api)
        self.assertFalse((outside / "new-entry").exists())

    def test_failed_command_retains_stdout_diagnostic(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("design_library_diagnostic_gallery", ROOT / "scripts/gallery.py")
        gallery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gallery)
        with self.assertRaisesRegex(RuntimeError, "synthetic preflight diagnostic"):
            gallery.command([sys.executable, "-c", "print('synthetic preflight diagnostic'); raise SystemExit(1)"])

    def test_nested_workspace_rejected(self):
        nested = self.repo / "nested"
        nested.mkdir()
        self.call("config", "set", "--workspace", str(nested))
        self.call("doctor", ok=False)


if __name__ == "__main__":
    unittest.main()
