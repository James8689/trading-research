"""Persistent, fail-closed simulated provider accounting; never dispatches calls.

Only an external controller may initialize or mutate this ledger. Worker outputs
are data, never ledger instructions. This is not OS isolation: another process
running as the same user can edit the database. No project API spend is approved
by this module; an uninitialized ledger has a zero allowance.
"""
from contextlib import contextmanager
from pathlib import Path
import sqlite3


def _amount(value):
    if type(value) is not int or value < 0 or value > 2**63 - 1:
        raise ValueError("amount must be a nonnegative signed-64-bit integer")
    return value


def _identifier(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("identifier must be a nonempty string")
    return value


class BudgetLedger:
    def __init__(self, root):
        self.path = Path(root) / "research_state" / "budget.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), period_id TEXT NOT NULL, limit_microusd INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS control (id INTEGER PRIMARY KEY CHECK(id=1), stopped INTEGER NOT NULL, reason TEXT)")
            db.execute("INSERT OR IGNORE INTO control VALUES (1,0,NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS attempts (attempt_id TEXT PRIMARY KEY, maximum_microusd INTEGER NOT NULL, state TEXT NOT NULL, provider_request_id TEXT, actual_microusd INTEGER)")

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self, period_id, limit_microusd):
        _identifier(period_id)
        _amount(limit_microusd)
        with self._transaction() as db:
            policy = db.execute("SELECT * FROM policy").fetchone()
            if policy and (policy["period_id"], policy["limit_microusd"]) != (period_id, limit_microusd):
                raise ValueError("ledger policy is immutable; cannot reset spend or raise allowance")
            db.execute("INSERT OR IGNORE INTO policy VALUES (1,?,?)", (period_id, limit_microusd))
            return self._status(db)

    @staticmethod
    def _status(db):
        policy = db.execute("SELECT * FROM policy").fetchone()
        control = db.execute("SELECT * FROM control").fetchone()
        attempts = [dict(row) for row in db.execute("SELECT * FROM attempts ORDER BY attempt_id")]
        spent = sum(row["actual_microusd"] for row in attempts if row["state"] == "settled")
        reserved = sum(row["maximum_microusd"] for row in attempts if row["state"] != "settled")
        unknown = sum(row["state"] == "unknown" for row in attempts)
        limit = policy["limit_microusd"] if policy else 0
        return {"period_id": policy["period_id"] if policy else None,
                "limit_microusd": limit, "spent_microusd": spent,
                "reserved_microusd": reserved, "available_microusd": max(0, limit-spent-reserved),
                "unknown_count": unknown, "stopped": bool(control["stopped"]),
                "stop_reason": control["reason"], "over_budget": spent + reserved > limit,
                "blocked": not policy or bool(control["stopped"]) or bool(unknown) or spent + reserved > limit,
                "attempts": attempts}

    def status(self):
        with self._transaction() as db:
            return self._status(db)

    @staticmethod
    def _attempt(db, attempt_id):
        row = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (_identifier(attempt_id),)).fetchone()
        if row is None:
            raise ValueError("unknown attempt")
        return dict(row)

    def reserve(self, attempt_id, maximum_microusd):
        _identifier(attempt_id)
        _amount(maximum_microusd)
        with self._transaction() as db:
            existing = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            if existing:
                if existing["maximum_microusd"] != maximum_microusd:
                    raise ValueError("conflicting reservation")
                return dict(existing)
            status = self._status(db)
            if status["blocked"] or maximum_microusd > status["available_microusd"]:
                raise RuntimeError("budget admission denied")
            db.execute("INSERT INTO attempts VALUES (?,?,'reserved',NULL,NULL)", (attempt_id, maximum_microusd))
            return self._attempt(db, attempt_id)

    def record_dispatch(self, attempt_id, provider_request_id):
        _identifier(provider_request_id)
        with self._transaction() as db:
            attempt = self._attempt(db, attempt_id)
            if attempt["provider_request_id"]:
                if attempt["provider_request_id"] != provider_request_id:
                    raise ValueError("conflicting dispatch receipt")
                return attempt
            if attempt["state"] != "reserved":
                raise ValueError("attempt no longer dispatchable")
            if self._status(db)["blocked"]:
                raise RuntimeError("dispatch accounting blocked")
            db.execute("UPDATE attempts SET state='dispatched', provider_request_id=? WHERE attempt_id=?", (provider_request_id, attempt_id))
            return self._attempt(db, attempt_id)

    def settle(self, attempt_id, actual_microusd):
        if actual_microusd is not None:
            _amount(actual_microusd)
        with self._transaction() as db:
            attempt = self._attempt(db, attempt_id)
            if attempt["state"] == "settled":
                if attempt["actual_microusd"] != actual_microusd:
                    raise ValueError("conflicting settlement")
                return attempt
            # Unknown/timeout outcomes keep the entire reservation until reconciled.
            db.execute("UPDATE attempts SET state=?, actual_microusd=? WHERE attempt_id=?",
                       ("unknown" if actual_microusd is None else "settled", actual_microusd, attempt_id))
            return self._attempt(db, attempt_id)

    def stop(self, reason):
        _identifier(reason)
        with self._transaction() as db:
            db.execute("UPDATE control SET stopped=1, reason=? WHERE id=1", (reason,))
            return self._status(db)

    def resume(self):
        with self._transaction() as db:
            db.execute("UPDATE control SET stopped=0, reason=NULL WHERE id=1")
            return self._status(db)
