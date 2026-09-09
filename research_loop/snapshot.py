"""Private operator backups, never worker packets or public/GitHub artifacts.

Contains evaluation answer keys and runtime records. Only the three runtime
databases are included, never arbitrary workspace files. Each SQLite backup is
consistent individually; this is NOT a cross-database atomic snapshot. Operators
must keep the manual runtime idle during export/restore (no background workers).
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile


DATABASES = ("network.sqlite3", "improvement.sqlite3", "budget.sqlite3")
MANIFEST = "manifest.json"


def _readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=30)


def _digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": value.hexdigest()}


def _validate_database(path):
    with closing(_readonly(path)) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("SQLite integrity check failed: " + path.name)


def _idle(db):
    if db.execute("SELECT COUNT(*) FROM tasks WHERE state='leased'").fetchone()[0]:
        raise ValueError("Finish or explicitly abandon leased tasks before exporting")


def export_snapshot(root, destination):
    root = Path(root).resolve()
    state = root / "research_state"
    destination = Path(destination).resolve()
    if destination.suffix.lower() != ".zip":
        raise ValueError("snapshot destination must end in .zip")
    if destination.is_relative_to(state.resolve()):
        raise ValueError("snapshot destination cannot be inside research_state")
    if destination.exists():
        raise FileExistsError(destination)
    for name in DATABASES:
        if not (state / name).is_file():
            raise ValueError("Initialize all three runtime databases before exporting")
    # Hold the network read transaction while copying. A task lease cannot be
    # committed through this connection's rollback-journal snapshot window.
    # Independent database writers still require the operator's idle discipline.
    with tempfile.TemporaryDirectory(prefix=".snapshot-export-", dir=root) as temporary:
        staging = Path(temporary)
        with closing(_readonly(state / DATABASES[0])) as network:
            network.execute("BEGIN")
            _idle(network)
            for name in DATABASES:
                with closing(sqlite3.connect(staging / name)) as target:
                    if name == DATABASES[0]:
                        network.backup(target)
                    else:
                        with closing(_readonly(state / name)) as source:
                            source.backup(target)
                _validate_database(staging / name)
        manifest = {
            "schema_version": 1,
            "classification": "private_operator_backup_contains_evaluation_keys",
            "consistency": "individual SQLite snapshots; no cross-database atomicity",
            "files": {name: _digest(staging / name) for name in DATABASES},
        }
        # Build fully before exclusive creation, preserving an existing archive.
        built = staging / "snapshot.zip"
        with zipfile.ZipFile(built, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MANIFEST, json.dumps(manifest, sort_keys=True, indent=2))
            for name in DATABASES:
                archive.write(staging / name, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with destination.open("xb") as output:
                created = True
                with built.open("rb") as source:
                    shutil.copyfileobj(source, output)
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            raise
    return {"archive": str(destination), "manifest": manifest, **_digest(destination)}


def restore_snapshot(root, archive):
    root = Path(root).resolve()
    archive = Path(archive).resolve()
    state = root / "research_state"
    root.mkdir(parents=True, exist_ok=True)

    def ensure_empty():
        for name in DATABASES:
            for suffix in ("", "-wal", "-shm", "-journal"):
                if (state / (name + suffix)).exists():
                    raise FileExistsError("Restore cannot overwrite existing runtime state")

    ensure_empty()
    with tempfile.TemporaryDirectory(prefix=".snapshot-restore-", dir=root) as temporary:
        staging = Path(temporary)
        with zipfile.ZipFile(archive, "r") as source:
            names = source.namelist()
            expected = set(DATABASES) | {MANIFEST}
            if len(names) != len(expected) or set(names) != expected:
                raise ValueError("Unexpected, missing, duplicate, or unsafe archive entries")
            manifest = json.loads(source.read(MANIFEST))
            if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int
                    or manifest["schema_version"] != 1
                    or manifest.get("classification") != "private_operator_backup_contains_evaluation_keys"
                    or not isinstance(manifest.get("files"), dict)
                    or set(manifest["files"]) != set(DATABASES)):
                raise ValueError("Invalid snapshot manifest")
            for name in DATABASES:
                metadata = manifest["files"][name]
                if (not isinstance(metadata, dict) or set(metadata) != {"bytes", "sha256"}
                        or type(metadata["bytes"]) is not int or metadata["bytes"] < 0
                        or not isinstance(metadata["sha256"], str)):
                    raise ValueError("Invalid snapshot file metadata")
                if source.getinfo(name).file_size != metadata["bytes"]:
                    raise ValueError("Snapshot size mismatch")
                # Exact allowlist paths, no extractall or archive-controlled paths.
                with source.open(name) as input_file, (staging / name).open("xb") as output:
                    shutil.copyfileobj(input_file, output)
                if _digest(staging / name) != metadata:
                    raise ValueError("Snapshot hash mismatch")
                _validate_database(staging / name)
        with closing(_readonly(staging / "network.sqlite3")) as db:
            _idle(db)
        ensure_empty()
        state.mkdir(parents=True, exist_ok=True)
        installed = []
        try:
            for name in DATABASES:
                target = state / name
                # Hard-link a fully validated staged file without overwrite. The
                # temporary name is removed automatically, leaving this link.
                target.hardlink_to(staging / name)
                installed.append(target)
        except BaseException:
            for target in installed:
                target.unlink()
            raise
    return {"root": str(root), "manifest": manifest, "restored": list(DATABASES)}
