"""A bounded, resumable, stdlib-only research-agent orchestrator.

This is intentionally a reasoning/review loop, not a trading system.  Worker
prompts forbid broker access, network orders, and repository changes.  The
manual backend is useful for a human or another model to execute one packet at
a time; the optional Codex backend is only a replaceable subprocess adapter.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Iterator, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    "max_cycles": 2,
    "max_calls": 12,
    "max_seconds_per_call": 300,
    "max_packet_chars": 20000,
    "models": {"worker": "gpt-5.6-luna", "frontier": "gpt-6-astra"},
    "backend": "manual",
    "max_total_tokens": 120000,
}

ROLES = ("scout", "mechanism", "data", "adversary", "coordinator")
DECISIONS = {"continue", "reject", "blocked", "review_required"}
TASK_STATUSES = {"pending", "running", "completed", "blocked", "failed"}
RESULT_KEYS = {
    "summary",
    "decision",
    "evidence",
    "next_action",
    "memory",
    "uncertainty",
}
LIMITS = {
    "summary": 4000,
    "next_action": 1500,
    "memory": 4000,
    "uncertainty": 1500,
}

POLICY = (
    "Research only. Do not place, simulate as if authorized to place, or submit "
    "broker orders. Do not contact brokers or acquire data over the network. Do "
    "not modify the repository. State uncertainty, point-in-time limits, costs, "
    "and validation gaps. This loop cannot promote a trading strategy."
)


class ResearchLoopError(RuntimeError):
    """A recoverable loop/configuration/state error."""


class ResultValidationError(ResearchLoopError, ValueError):
    """A worker result does not conform to the exact result contract."""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(_json_dump(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name)
        raise


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except FileNotFoundError:
        if default is not None:
            return default
        raise ResearchLoopError(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        raise ResearchLoopError(f"Invalid JSON in {path}: {exc}") from exc


def _safe_name(value: str) -> str:
    if not value or Path(value).name != value or value in {".", ".."}:
        raise ResearchLoopError(f"Unsafe task id: {value!r}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(char not in allowed for char in value):
        raise ResearchLoopError(f"Unsafe task id: {value!r}")
    return value


def _inside(root: Path, path: Path) -> Path:
    root = root.resolve()
    candidate = path.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ResearchLoopError(f"Path escapes research root: {path}") from exc
    return candidate


class _FileLock:
    """Exclusive lock based on atomic file creation (works on Windows too)."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> "_FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = _json_dump({"pid": os.getpid(), "started_at": _now()}).encode("utf-8")
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ResearchLoopError(f"Another research loop is already running: {self.path}") from exc
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                self.path.unlink()
            raise
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.path.unlink()


def validate_result(value: Any) -> dict[str, Any]:
    """Validate a worker's exact JSON result contract and return a copy."""
    if not isinstance(value, dict):
        raise ResultValidationError("Result must be a JSON object")
    if set(value) != RESULT_KEYS:
        missing = sorted(RESULT_KEYS - set(value))
        extra = sorted(set(value) - RESULT_KEYS)
        raise ResultValidationError(f"Result keys must be exactly {sorted(RESULT_KEYS)}; missing={missing}, extra={extra}")
    for field, limit in LIMITS.items():
        if not isinstance(value[field], str):
            raise ResultValidationError(f"{field} must be a string")
        if len(value[field]) > limit:
            raise ResultValidationError(f"{field} exceeds {limit} characters")
    if value["decision"] not in DECISIONS:
        raise ResultValidationError(f"decision must be one of {sorted(DECISIONS)}")
    evidence = value["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 20 or any(not isinstance(item, str) for item in evidence):
        raise ResultValidationError("evidence must be a list of at most 20 strings")
    return dict(value)


class ResearchLoop:
    """Durable state manager and bounded task scheduler rooted at ``root``."""

    def __init__(self, root: os.PathLike[str] | str):
        self.root = Path(root).expanduser().resolve()
        self.state_dir = self.root / "research_state"
        self.state_path = self.state_dir / "state.json"
        self.config_path = self.root / "config" / "agent_network.json"
        self.lock_path = self.state_dir / ".lock"

    @property
    def config(self) -> dict[str, Any]:
        config = _read_json(self.config_path, default=DEFAULT_CONFIG)
        if not isinstance(config, dict):
            raise ResearchLoopError("agent_network.json must contain an object")
        merged = json.loads(_json_dump(DEFAULT_CONFIG))
        merged.update(config)
        merged["models"] = {**DEFAULT_CONFIG["models"], **(config.get("models") or {})}
        for key in ("max_cycles", "max_calls", "max_seconds_per_call", "max_packet_chars", "max_total_tokens"):
            if not isinstance(merged[key], int) or merged[key] <= 0:
                raise ResearchLoopError(f"config {key} must be a positive integer")
        if merged.get("backend") not in {"manual", "codex"}:
            raise ResearchLoopError("config backend must be manual or codex")
        return merged

    def init(self, *, overwrite: bool = False) -> dict[str, Any]:
        """Create the durable layout and initial state; preserve existing state by default."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if overwrite or not self.config_path.exists():
            _atomic_json(self.config_path, DEFAULT_CONFIG)
        if overwrite or not self.state_path.exists():
            state = self._new_state()
            _atomic_json(self.state_path, state)
            self._event("initialized", {"state": str(self.state_path)})
        for role in ROLES:
            memory = self.state_dir / "memory" / f"{role}.md"
            if not memory.exists():
                memory.parent.mkdir(parents=True, exist_ok=True)
                memory.write_text("", encoding="utf-8")
        return self.state()

    def _new_state(self) -> dict[str, Any]:
        return {
            "version": 1,
            "created_at": _now(),
            "updated_at": _now(),
            "cycle": 0,
            "tasks": {},
            "calls": 0,
            "reserved_tokens": 0,
            "used_tokens": 0,
            "usage_unknown": False,
            "stopped": False,
            "stop_reason": None,
            "outcome": None,
        }

    def state(self) -> dict[str, Any]:
        state = _read_json(self.state_path)
        if not isinstance(state, dict) or not isinstance(state.get("tasks"), dict):
            raise ResearchLoopError("state.json has an invalid shape")
        return state

    def status(self) -> dict[str, Any]:
        state = self.state()
        counts = {status: 0 for status in TASK_STATUSES}
        for task in state["tasks"].values():
            status = task.get("status")
            if status in counts:
                counts[status] += 1
        return {**state, "counts": counts, "config": self.config}

    def _save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = _now()
        _atomic_json(self.state_path, state)

    def _event(self, event: str, data: Mapping[str, Any] | None = None, *, task_id: str | None = None) -> None:
        record = {"at": _now(), "event": event, **(dict(data or {}))}
        paths = [self.state_dir / "events.jsonl"]
        if task_id:
            paths.append(self.task_dir(task_id) / "events.jsonl")
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")

    def task_dir(self, task_id: str) -> Path:
        return _inside(self.state_dir, self.state_dir / "tasks" / _safe_name(task_id))

    def _stop_if_requested(self, state: dict[str, Any]) -> bool:
        stop = self.state_dir / "STOP"
        if stop.exists():
            state["stopped"] = True
            state["stop_reason"] = "STOP file exists"
            self._save(state)
            self._event("stopped", {"reason": state["stop_reason"]})
            return True
        return bool(state.get("stopped"))

    def _ensure_cycle(self, state: dict[str, Any]) -> None:
        config = self.config
        if state.get("stopped"):
            return
        active = [task for task in state["tasks"].values() if task.get("status") in {"pending", "running"}]
        if active:
            return
        completed_coordinators = [
            task for task in state["tasks"].values()
            if task.get("role") == "coordinator" and task.get("status") == "completed"
        ]
        if completed_coordinators and state.get("outcome") in {"reject", "blocked"}:
            state["stopped"] = True
            state["stop_reason"] = f"Coordinator decision: {state['outcome']}"
            return
        if state.get("cycle", 0) >= config["max_cycles"]:
            state["stopped"] = True
            state["stop_reason"] = "max_cycles reached"
            return
        cycle = int(state.get("cycle", 0)) + 1
        state["cycle"] = cycle
        prefix = f"cycle-{cycle:03d}"
        specs = {
            "scout": [],
            "mechanism": [f"{prefix}-scout"],
            "data": [f"{prefix}-scout"],
            "adversary": [f"{prefix}-mechanism", f"{prefix}-data"],
            "coordinator": [f"{prefix}-adversary"],
        }
        for role in ROLES:
            task_id = f"{prefix}-{role}"
            state["tasks"][task_id] = {
                "id": task_id,
                "cycle": cycle,
                "role": role,
                "status": "pending",
                "depends_on": specs[role],
                "created_at": _now(),
                "packet_path": None,
                "result_path": None,
                "memory_path": str(self.state_dir / "memory" / f"{role}.md"),
                "decision": None,
                "error": None,
            }
        self._event("cycle_created", {"cycle": cycle, "tasks": [f"{prefix}-{role}" for role in ROLES]})

    def _ready_tasks(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        ready = []
        for task in state["tasks"].values():
            if task.get("status") != "pending":
                continue
            dependencies = [state["tasks"].get(dep) for dep in task.get("depends_on", [])]
            if any(dep is None for dep in dependencies):
                continue
            if any(dep.get("status") in {"blocked", "failed"} for dep in dependencies):
                task["status"] = "blocked"
                task["error"] = "dependency did not complete"
                continue
            if all(dep.get("status") == "completed" for dep in dependencies):
                ready.append(task)
        return sorted(ready, key=lambda task: (task["cycle"], ROLES.index(task["role"]), task["id"]))

    def _role_prompt(self, role: str) -> str:
        path = self.root / "agents" / "prompts" / f"{role}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        defaults = {
            "scout": "Propose one original, falsifiable research question and its economic mechanism.",
            "mechanism": "Inspect the proposed mechanism, required observables, and point-in-time data needs.",
            "data": "Audit whether the mechanism can be tested with available, timestamped, survivorship-aware data.",
            "adversary": "Try to falsify the proposal: costs, lookahead, selection, concentration, and alternative explanations.",
            "coordinator": "Synthesize the evidence and decide whether bounded research should continue, be rejected, blocked, or receive review.",
        }
        return defaults[role]

    def _memory(self, role: str) -> str:
        path = self.state_dir / "memory" / f"{role}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")[-4000:]

    def _dependency_summary(self, state: dict[str, Any], task: dict[str, Any]) -> list[dict[str, Any]]:
        summaries = []
        for dep_id in task.get("depends_on", []):
            dep = state["tasks"][dep_id]
            result_path = dep.get("result_path")
            result = _read_json(Path(result_path)) if result_path and Path(result_path).exists() else {}
            summaries.append({
                "task": dep_id,
                "role": dep.get("role"),
                "summary": str(result.get("summary", ""))[:4000],
                "decision": result.get("decision"),
                "evidence": result.get("evidence", [])[:20],
                "next_action": str(result.get("next_action", ""))[:1500],
                "uncertainty": str(result.get("uncertainty", ""))[:1500],
            })
        return summaries

    def _packet(self, state: dict[str, Any], task: dict[str, Any]) -> str:
        payload = {
            "task_id": task["id"],
            "cycle": task["cycle"],
            "role": task["role"],
            "policy": POLICY,
            "role_prompt": self._role_prompt(task["role"]),
            "own_previous_compact_memory": self._memory(task["role"]),
            "dependency_summaries": self._dependency_summary(state, task),
            "result_schema": {
                "summary": "string <=4000 characters",
                "decision": "continue|reject|blocked|review_required",
                "evidence": "list[string], max 20",
                "next_action": "string <=1500 characters",
                "memory": "string <=4000 characters",
                "uncertainty": "string <=1500 characters",
            },
            "constraints": [
                "Return exactly the result_schema keys as JSON.",
                "Do not invent source access, fills, returns, or validation.",
                "A coordinator decision never authorizes trading or promotes a strategy.",
            ],
        }
        header = "# Research task packet\n\n"
        text = header + json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        limit = self.config["max_packet_chars"]
        if len(text) <= limit:
            return text
        # Keep the packet contract intact while clipping only context fields.
        payload["own_previous_compact_memory"] = str(payload["own_previous_compact_memory"])[-1000:]
        payload["role_prompt"] = str(payload["role_prompt"])[:2000]
        for item in payload["dependency_summaries"]:
            item["summary"] = str(item["summary"])[:1000]
            item["evidence"] = item["evidence"][:5]
            item["next_action"] = str(item["next_action"])[:500]
            item["uncertainty"] = str(item["uncertainty"])[:500]
        text = header + json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if len(text) > limit:
            raise ResearchLoopError(f"Unable to fit task packet under max_packet_chars={limit}")
        return text

    def next_packet(self) -> str | None:
        """Claim and write one ready packet, returning its text; return None when stopped."""
        with _FileLock(self.lock_path):
            state = self.state()
            if self._stop_if_requested(state):
                return None
            self._ensure_cycle(state)
            if state.get("stopped"):
                self._save(state)
                return None
            ready = self._ready_tasks(state)
            if not ready:
                if any(task.get("status") in {"failed", "blocked"} for task in state["tasks"].values()):
                    state["stopped"] = True
                    state["stop_reason"] = "A task failed or was blocked; no automatic retry"
                self._save(state)
                return None
            task = ready[0]
            packet = self._packet(state, task)
            task_dir = self.task_dir(task["id"])
            task_dir.mkdir(parents=True, exist_ok=True)
            packet_path = task_dir / "packet.md"
            packet_path.write_text(packet, encoding="utf-8")
            task["status"] = "running"
            task["started_at"] = _now()
            task["packet_path"] = str(packet_path)
            self._save(state)
            self._event("task_claimed", {"role": task["role"], "cycle": task["cycle"]}, task_id=task["id"])
            return packet

    def submit(self, task_id: str, result: Mapping[str, Any] | str | os.PathLike[str]) -> dict[str, Any]:
        """Validate and durably submit a result for a claimed task."""
        task_id = _safe_name(task_id)
        if isinstance(result, (str, os.PathLike)):
            candidate = Path(result)
            path = _inside(self.root, candidate if candidate.is_absolute() else self.root / candidate)
            result_value = _read_json(path)
        else:
            result_value = dict(result)
        checked = validate_result(result_value)
        with _FileLock(self.lock_path):
            state = self.state()
            task = state["tasks"].get(task_id)
            if not task:
                raise ResearchLoopError(f"Unknown task: {task_id}")
            if task.get("status") != "running":
                raise ResearchLoopError(f"Task {task_id} is {task.get('status')}, expected running")
            task_dir = self.task_dir(task_id)
            task_dir.mkdir(parents=True, exist_ok=True)
            result_path = task_dir / "result.json"
            _atomic_json(result_path, checked)
            memory_path = self.state_dir / "memory" / f"{task['role']}.md"
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            memory_path.write_text(checked["memory"], encoding="utf-8")
            task.update({
                "status": "completed" if checked["decision"] != "blocked" else "blocked",
                "completed_at": _now(),
                "result_path": str(result_path),
                "decision": checked["decision"],
                "error": None,
            })
            if task["role"] == "coordinator":
                state["outcome"] = checked["decision"]
                if checked["decision"] in {"reject", "blocked"}:
                    state["stopped"] = True
                    state["stop_reason"] = f"Coordinator decision: {checked['decision']}"
            self._save(state)
            self._event("task_submitted", {"decision": checked["decision"]}, task_id=task_id)
            return checked

    def _budget_available(self, state: dict[str, Any], estimated: int) -> None:
        config = self.config
        if state.get("usage_unknown"):
            raise ResearchLoopError("Provider token usage is unknown; paid dispatch is stopped")
        if state.get("calls", 0) >= config["max_calls"]:
            raise ResearchLoopError("max_calls reached")
        if state.get("reserved_tokens", 0) + estimated > config["max_total_tokens"]:
            raise ResearchLoopError("max_total_tokens would be exceeded by this dispatch")

    @staticmethod
    def _usage_from_output(output: str) -> int | None:
        usage: int | None = None
        for line in output.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("type") != "turn.completed":
                continue
            raw = item.get("usage") or item.get("turn", {}).get("usage")
            if not isinstance(raw, dict):
                continue
            total = raw.get("total_tokens")
            if isinstance(total, int):
                usage = total
            elif isinstance(raw.get("input_tokens"), int) and isinstance(raw.get("output_tokens"), int):
                usage = raw["input_tokens"] + raw["output_tokens"]
        return usage

    def _dispatch_codex(self, task: dict[str, Any], packet: str, state: dict[str, Any]) -> dict[str, Any]:
        config = self.config
        task_dir = self.task_dir(task["id"])
        schema_path = task_dir / "output_schema.json"
        _atomic_json(schema_path, {"type": "object", "additionalProperties": False, "required": sorted(RESULT_KEYS), "properties": {
            "summary": {"type": "string", "maxLength": 4000},
            "decision": {"type": "string", "enum": sorted(DECISIONS)},
            "evidence": {"type": "array", "maxItems": 20, "items": {"type": "string"}},
            "next_action": {"type": "string", "maxLength": 1500},
            "memory": {"type": "string", "maxLength": 4000},
            "uncertainty": {"type": "string", "maxLength": 1500},
        }})
        result_path = task_dir / "codex-result.json"
        estimated = max(1, (len(packet) + 3) // 4)
        state["reserved_tokens"] = state.get("reserved_tokens", 0) + estimated
        state["calls"] = state.get("calls", 0) + 1
        self._save(state)
        command = os.environ.get("CODEX_COMMAND", "codex")
        argv = [command, "--ignore-user-config", "--ephemeral", "--sandbox", "read-only", "--json", "--output-schema", str(schema_path), "-o", str(result_path), "--model", str(config["models"].get("frontier" if task["role"] == "coordinator" else "worker"))]
        try:
            completed = subprocess.run(argv, input=packet, text=True, capture_output=True, timeout=config["max_seconds_per_call"], shell=False, cwd=str(self.root), check=False)
        except subprocess.TimeoutExpired as exc:
            task["status"] = "failed"
            task["error"] = "uncertain_timeout; no automatic retry"
            state["usage_unknown"] = True
            self._save(state)
            self._event("task_timeout", {"error": task["error"]}, task_id=task["id"])
            raise ResearchLoopError(task["error"]) from exc
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        used = self._usage_from_output(output)
        if used is None:
            state["usage_unknown"] = True
        else:
            state["used_tokens"] = state.get("used_tokens", 0) + used
        if completed.returncode != 0:
            task["status"] = "failed"
            task["error"] = f"codex exited {completed.returncode}"
            self._save(state)
            self._event("task_failed", {"error": task["error"]}, task_id=task["id"])
            raise ResearchLoopError(task["error"])
        if result_path.exists():
            value = _read_json(result_path)
        else:
            # Some adapters emit the JSON object as a JSONL event instead of honoring -o.
            candidates = []
            for line in (completed.stdout or "").splitlines():
                with contextlib.suppress(json.JSONDecodeError):
                    item = json.loads(line)
                    if isinstance(item, dict) and RESULT_KEYS.issubset(item):
                        candidates.append(item)
            if not candidates:
                task["status"] = "failed"
                task["error"] = "codex produced no result JSON"
                self._save(state)
                raise ResearchLoopError(task["error"])
            value = candidates[-1]
        self._save(state)
        return validate_result(value)

    def run(self, *, backend: str | None = None) -> str | None:
        """Run one manual packet or bounded Codex loop.

        Manual mode claims one task, prints/returns its packet, and deliberately
        stops. Codex mode resumes until a stop condition or coordinator outcome.
        """
        backend = backend or self.config["backend"]
        if backend not in {"manual", "codex"}:
            raise ResearchLoopError(f"Unsupported backend: {backend}")
        if backend == "manual":
            return self.next_packet()
        while True:
            packet = self.next_packet()
            if packet is None:
                return None
            state = self.state()
            running = [task for task in state["tasks"].values() if task.get("status") == "running"]
            if not running:
                raise ResearchLoopError("scheduler claimed no task")
            task = sorted(running, key=lambda item: item["started_at"])[-1]
            with _FileLock(self.lock_path):
                state = self.state()
                task = state["tasks"][task["id"]]
                try:
                    result = self._dispatch_codex(task, packet, state)
                except ResultValidationError as exc:
                    task["status"] = "failed"
                    task["error"] = str(exc)
                    self._save(state)
                    self._event("task_failed", {"error": str(exc)}, task_id=task["id"])
                    raise
            self.submit(task["id"], result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded, research-only agent loop")
    parser.add_argument("--root", default=".", help="research project root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("next")
    submit = sub.add_parser("submit")
    submit.add_argument("task_id")
    submit.add_argument("result", nargs="?", help="JSON result path; defaults to stdin")
    run = sub.add_parser("run")
    run.add_argument("--backend", choices=("manual", "codex"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    loop = ResearchLoop(args.root)
    try:
        if args.command == "init":
            value = loop.init()
        elif args.command == "status":
            value = loop.status()
        elif args.command == "next":
            value = loop.next_packet()
        elif args.command == "submit":
            if args.result:
                value = loop.submit(args.task_id, args.result)
            else:
                value = loop.submit(args.task_id, json.load(sys.stdin))
        elif args.command == "run":
            value = loop.run(backend=args.backend)
        else:
            raise ResearchLoopError("unknown command")
        if isinstance(value, str):
            sys.stdout.write(value)
        else:
            sys.stdout.write(_json_dump(value))
        return 0
    except (ResearchLoopError, OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"research_loop: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
