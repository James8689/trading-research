import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from research_loop.budget import BudgetLedger
from research_loop.improvement import ImprovementRegistry
from research_loop.network import Network
from research_loop.snapshot import DATABASES, export_snapshot, restore_snapshot


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "original"
        self.network = Network(self.root)
        self.network.initialize()
        self.cycle = self.network.create_cycle("fixture", "Check fixture.", [], "a" * 64)
        packet = self.network.claim("director", "director_plan")
        self.network.fail(packet["task_id"], "director", "Preserved fixture failure")
        self.registry = ImprovementRegistry(self.root)
        self.registry.initialize()
        version = self.registry.register("researcher", "Initial fixture prompt")
        self.registry.bootstrap(version["id"])
        self.budget = BudgetLedger(self.root)
        self.budget.initialize("simulation", 100)
        self.budget.reserve("pending-charge", 30)
        self.archive = self.base / "operator.zip"

    def test_roundtrip_preserves_attempts_versions_and_reservations(self):
        exported = export_snapshot(self.root, self.archive)
        self.assertEqual(set(exported["manifest"]["files"]), set(DATABASES))
        restored_root = self.base / "restored"
        restore_snapshot(restored_root, self.archive)
        self.assertEqual(Network(restored_root).status(), self.network.status())
        self.assertEqual(ImprovementRegistry(restored_root).status(), self.registry.status())
        self.assertEqual(BudgetLedger(restored_root).status(), self.budget.status())

    def test_export_refuses_lease(self):
        self.network.create_cycle("fixture2", "Check another fixture.", [], "b" * 64)
        self.assertIsNotNone(self.network.claim("second-director", "director_plan"))
        with self.assertRaises(ValueError):
            export_snapshot(self.root, self.archive)
        self.assertFalse(self.archive.exists())

    def test_existing_state_and_archive_never_overwritten(self):
        export_snapshot(self.root, self.archive)
        before = self.archive.read_bytes()
        with self.assertRaises(FileExistsError):
            export_snapshot(self.root, self.archive)
        with self.assertRaises(FileExistsError):
            restore_snapshot(self.root, self.archive)
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertEqual(self.budget.status()["reserved_microusd"], 30)

    def test_destination_scope_and_suffix(self):
        for path in [self.root / "research_state" / "backup.zip", self.base / "backup.txt"]:
            with self.assertRaises(ValueError):
                export_snapshot(self.root, path)

    def _rewrite(self, transform):
        export_snapshot(self.root, self.archive)
        with zipfile.ZipFile(self.archive) as source:
            entries = [(name, source.read(name)) for name in source.namelist()]
        target = self.base / "tampered.zip"
        with zipfile.ZipFile(target, "w") as output:
            for name, data in transform(entries):
                output.writestr(name, data)
        return target

    def test_path_traversal_rejected_before_install(self):
        archive = self._rewrite(lambda entries: entries + [("../escaped", b"bad")])
        destination = self.base / "restored"
        with self.assertRaises(ValueError):
            restore_snapshot(destination, archive)
        self.assertFalse((self.base / "escaped").exists())
        self.assertFalse((destination / "research_state").exists())

    def test_tampered_hash_rejected_before_install(self):
        def tamper(entries):
            result = []
            for name, data in entries:
                if name == "manifest.json":
                    manifest = json.loads(data)
                    manifest["files"]["budget.sqlite3"]["sha256"] = "0" * 64
                    data = json.dumps(manifest).encode()
                result.append((name, data))
            return result

        archive = self._rewrite(tamper)
        destination = self.base / "restored"
        with self.assertRaises(ValueError):
            restore_snapshot(destination, archive)
        self.assertFalse((destination / "research_state").exists())

    def test_missing_database_rejected(self):
        archive = self._rewrite(lambda entries: [(n, d) for n, d in entries if n != "budget.sqlite3"])
        with self.assertRaises(ValueError):
            restore_snapshot(self.base / "restored", archive)


if __name__ == "__main__":
    unittest.main()
