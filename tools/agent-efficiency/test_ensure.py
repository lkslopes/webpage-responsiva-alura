"""Offline regression tests: no downloads, package installation or inference."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import ensure


class BootstrapTests(unittest.TestCase):
    def test_existing_installation_is_not_reinstalled(self):
        with patch.object(ensure, "discover", return_value=Path("tool")), \
             patch.object(Path, "is_file", return_value=True), \
             patch.object(ensure, "run", return_value='{"version":"4.0.1"}'), \
             patch.object(ensure, "install_rtk") as rtk, \
             patch.object(ensure, "install_headroom") as headroom, \
             patch.object(ensure, "install_caveman") as caveman:
            result = ensure.ensure()
            self.assertTrue(result["installation_ready"])
            for install in (rtk, headroom, caveman):
                install.assert_not_called()
            self.assertEqual(result["integration"], "not_verified")

    def test_missing_tools_are_installed_and_rechecked(self):
        installed = set()
        def discover(name):
            return Path(name) if name in installed else None
        with patch.object(ensure, "discover", side_effect=discover), \
             patch.object(Path, "is_file", return_value=True), \
             patch.object(ensure, "run", return_value='{"version":"4.0.1"}'), \
             patch.object(ensure, "install_rtk", side_effect=lambda: installed.add("rtk")), \
             patch.object(ensure, "install_headroom", side_effect=lambda: installed.add("headroom")), \
             patch.object(ensure, "install_caveman", side_effect=lambda: installed.add("caveman")):
            result = ensure.ensure()
            self.assertEqual(installed, {"rtk", "headroom", "caveman"})
            self.assertTrue(result["installation_ready"])
            self.assertTrue(all(t["status"] == "installed_now" for t in result["tools"].values()))

    def test_check_never_installs(self):
        with patch.object(ensure, "discover", return_value=None), \
             patch.object(ensure, "install_rtk") as installer:
            result = ensure.ensure(check=True)
            installer.assert_not_called()
            self.assertFalse(result["installation_ready"])

    def test_one_failure_does_not_skip_other_tools(self):
        with patch.object(ensure, "discover", return_value=None), \
             patch.object(ensure, "install_rtk", side_effect=RuntimeError("network denied")), \
             patch.object(ensure, "install_headroom") as headroom, \
             patch.object(ensure, "install_caveman") as caveman:
            result = ensure.ensure()
            headroom.assert_called_once()
            caveman.assert_called_once()
            self.assertFalse(result["installation_ready"])
            self.assertEqual(result["tools"]["rtk"]["reason"], "network denied")

    def test_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "SHA256 mismatch"):
            ensure.extract_rtk(b"changed", "rtk.zip", "0" * 64)

    def test_archive_paths_are_not_extracted(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("../../rtk.exe", b"binary")
            archive.writestr("../../unrelated.txt", b"not extracted")
        raw = data.getvalue()
        self.assertEqual(ensure.extract_rtk(raw, "rtk.zip", hashlib.sha256(raw).hexdigest()), b"binary")

    def test_missing_companions_trigger_official_install_only(self):
        available = [False]
        calls = []
        def run(args, timeout=30):
            calls.append([str(a) for a in args])
            if "--install" in args:
                available[0] = True
            return '{"version":"4.0.1"}'
        with patch.object(ensure, "discover", return_value=Path("tool")), \
             patch.object(Path, "is_file", side_effect=lambda: available[0]), \
             patch.object(ensure, "run", side_effect=run):
            self.assertTrue(ensure.ensure()["installation_ready"])
        self.assertEqual(calls[0], ["tool", "setup", "--install", "--json"])
        self.assertFalse(any("enable" in c or "--agent-native" in c for c in calls))

    def test_concurrent_install_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(ensure, "ROOT", Path(directory)), \
             patch.object(ensure.sys, "argv", ["ensure.py"]), \
             patch.object(ensure, "ensure") as installer:
            (Path(directory) / "install.lock").write_text("another session")
            self.assertEqual(ensure.main(), 2)
            installer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
