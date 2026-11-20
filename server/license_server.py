#!/usr/bin/env python3
"""
License & per-device delivery server (stdlib-only).

Purpose:
- Enforce 1 license = 1 active device (1 goi / 1 khach / 1 SDT Vietlott SMS / 1 thiet bi).
- Deliver daily plan/SMS commands ONLY to activated, authorized devices via API.
- Support device change (rebind): 150,000 VND per change, verification, cooldown, audit log.

SECURITY/OPS NOTES:
- Run behind HTTPS (reverse proxy). Do NOT expose over plain HTTP on the internet.
- Set ADMIN_TOKEN to a strong secret; admin endpoints/CLI actions must be protected.
- Keep the SQLite DB (server/licenses.db by default) PRIVATE and backed up.
- Do NOT publish per-day commands to public repos/files/URLs. Commands are value.
- SMS to 9969 must be sent from the customer's Vietlott-registered phone number (Vietlott rule).

This is a pragmatic scaffold. Integrate payment verification (e.g. SePay webhook) and
per-customer configuration as your operations mature.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# --- Paths & imports ---
SERVER_DIR = Path(__file__).resolve().parent
ROOT_DIR = SERVER_DIR.parent
DEFAULT_DB = SERVER_DIR / "licenses.db"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- Policy (official) ---
REBIND_FEE_VND = 150_000
REBIND_COOLDOWN_DAYS = 30
MAX_ACTIVE_DEVICES_PER_LICENSE = 1

ADMIN_TOKEN_ENV = "ADMIN_TOKEN"
DB_PATH_ENV = "LICENSE_DB_PATH"
PORT_ENV = "LICENSE_SERVER_PORT"
HOST_ENV = "LICENSE_SERVER_HOST"


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def utcnow_iso() -> str:
    return utcnow().replace(microsecond=0).isoformat()


def parse_iso(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        # accept ...Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d
    except Exception:
        return None


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def gen_license_key() -> str:
    # URL/typing friendly, unambiguous-ish
    raw = secrets.token_hex(8).upper()
    return f"VAF-{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"


def gen_device_secret() -> str:
    return secrets.token_urlsafe(32)


def get_db_path(cli_path: Optional[str] = None) -> Path:
    p = cli_path or os.environ.get(DB_PATH_ENV)
    return Path(p) if p else DEFAULT_DB


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


SCHEMA = r"""
CREATE TABLE IF NOT EXISTS licenses (
    license_key TEXT PRIMARY KEY,
    customer_name TEXT,
    phone_vietlott TEXT,
    status TEXT NOT NULL DEFAULT 'active', -- active|suspended|revoked|expired
    package TEXT NOT NULL DEFAULT 'lifetime',
    config_json TEXT, -- per-customer config (game, quantity, numbers prefs, etc.)
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    device_id_hash TEXT NOT NULL,
    device_secret_hash TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    activated_at TEXT NOT NULL,
    revoked_at TEXT,
    last_seen_at TEXT,
    client_info TEXT,
    UNIQUE(license_key, device_id_hash)
);

CREATE INDEX IF NOT EXISTS idx_devices_license_active ON devices(license_key, active);

CREATE TABLE IF NOT EXISTS rebinds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    old_device_hash TEXT,
    new_device_hash TEXT,
    fee_vnd INTEGER NOT NULL DEFAULT 150000,
    paid_ref TEXT,
    reason TEXT,
    admin_note TEXT,
    cooldown_until TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT,
    device_id_hash TEXT,
    action TEXT NOT NULL,
    ok INTEGER NOT NULL,
    detail TEXT,
    ip TEXT,
    created_at TEXT NOT NULL
);
"""


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    # forward-safe simple migrations
    cols = {r[1] for r in conn.execute("PRAGMA table_info(licenses)").fetchall()}
    if "config_json" not in cols:
        conn.execute("ALTER TABLE licenses ADD COLUMN config_json TEXT")
    if "package" not in cols:
        conn.execute("ALTER TABLE licenses ADD COLUMN package TEXT NOT NULL DEFAULT 'lifetime'")


def log_access(conn: sqlite3.Connection, license_key: Optional[str], device_id: Optional[str],
               action: str, ok: bool, detail: str = "", ip: str = "") -> None:
    try:
        conn.execute(
            "INSERT INTO access_logs(license_key, device_id_hash, action, ok, detail, ip, created_at) VALUES (?,?,?,?,?,?,?)",
            (license_key, sha256_hex(device_id) if device_id else None, action, 1 if ok else 0,
             (detail or "")[:500], ip or "", utcnow_iso()),
        )
    except Exception:
        pass


def get_license(conn: sqlite3.Connection, license_key: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()


def get_active_device(conn: sqlite3.Connection, license_key: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM devices WHERE license_key = ? AND active = 1 ORDER BY activated_at DESC LIMIT 1",
        (license_key,),
    ).fetchone()


def get_device(conn: sqlite3.Connection, license_key: str, device_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM devices WHERE license_key = ? AND device_id_hash = ?",
        (license_key, sha256_hex(device_id)),
    ).fetchone()


def license_allows_access(lic: sqlite3.Row) -> Tuple[bool, str]:
    status = (lic["status"] or "").lower()
    if status != "active":
        return False, f"license_status_{status or 'unknown'}"
    return True, "ok"


def last_rebind(conn: sqlite3.Connection, license_key: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM rebinds WHERE license_key = ? ORDER BY id DESC LIMIT 1",
        (license_key,),
    ).fetchone()


def can_rebind_now(conn: sqlite3.Connection, license_key: str, now: Optional[dt.datetime] = None) -> Tuple[bool, str, Optional[str]]:
    now = now or utcnow()
    rb = last_rebind(conn, license_key)
    if not rb:
        return True, "ok", None
    until = parse_iso(rb["cooldown_until"]) if "cooldown_until" in rb.keys() else None
    if until and now < until:
        return False, "cooldown_active", until.isoformat()
    return True, "ok", (until.isoformat() if until else None)


def _load_daily_plan_for_today(license_row: sqlite3.Row) -> Dict[str, Any]:
    """Generate today's plan server-side for the bound license. Never read from public files."""
    # Lazy imports to avoid hard failure for admin-only DB ops if deps missing
    try:
        from cloud_daily_runner import run_daily_cloud_pipeline  # type: ignore
    except Exception as exc:
        return {"status": "ERROR", "message": f"plan_generator_unavailable: {exc}"}

    # Per-customer personalization (game, ticket_count/mode, custom numbers) via licenses.config_json
    config: Dict[str, Any] = {}
    raw_cfg = license_row["config_json"] if "config_json" in license_row.keys() else None
    if raw_cfg:
        try:
            config = json.loads(raw_cfg) if isinstance(raw_cfg, str) else (raw_cfg or {})
        except Exception:
            config = {}

    try:
        plan = run_daily_cloud_pipeline(config=config, write_files=False)
    except Exception as exc:
        return {"status": "ERROR", "message": f"plan_generation_failed: {exc}"}

    # Attach policy metadata for client clarity
    plan["delivery"] = {
        "bound_device_only": True,
        "generated_at": utcnow_iso(),
        "note": "Commands are issued only to the activated device for this license.",
    }
    return plan


class LicenseService:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        init_db(db_path)
        self._lock = threading.Lock()

    # ---- admin operations ----
    def create_license(self, customer_name: str = "", phone_vietlott: str = "", notes: str = "",
                       license_key: Optional[str] = None, config_json: Optional[str] = None) -> Dict[str, Any]:
        key = (license_key or gen_license_key()).strip().upper()
        now = utcnow_iso()
        with self._lock, connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO licenses(license_key, customer_name, phone_vietlott, status, package, config_json, notes, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (key, customer_name or None, phone_vietlott or None, "active", "lifetime", config_json, notes or None, now, now),
            )
        return {"ok": True, "license_key": key, "status": "active", "policy": {"max_active_devices": MAX_ACTIVE_DEVICES_PER_LICENSE, "rebind_fee_vnd": REBIND_FEE_VND, "rebind_cooldown_days": REBIND_COOLDOWN_DAYS}}

    def set_license_status(self, license_key: str, status: str) -> Dict[str, Any]:
        status = status.lower()
        if status not in {"active", "suspended", "revoked", "expired"}:
            return {"ok": False, "error": "invalid_status"}
        with self._lock, connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE licenses SET status=?, updated_at=? WHERE license_key=?",
                (status, utcnow_iso(), license_key.upper()),
            )
            if cur.rowcount == 0:
                return {"ok": False, "error": "license_not_found"}
        return {"ok": True, "license_key": license_key.upper(), "status": status}

    def set_license_config(self, license_key: str, config: Any) -> Dict[str, Any]:
        key = license_key.upper()
        if isinstance(config, str):
            try:
                parsed = json.loads(config) if config.strip() else None
                config_json = json.dumps(parsed, ensure_ascii=False) if parsed is not None else None
            except Exception:
                return {"ok": False, "error": "invalid_config_json"}
        elif isinstance(config, dict):
            config_json = json.dumps(config, ensure_ascii=False)
        elif config is None:
            config_json = None
        else:
            return {"ok": False, "error": "invalid_config"}
        with self._lock, connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE licenses SET config_json=?, updated_at=? WHERE license_key=?",
                (config_json, utcnow_iso(), key),
            )
            if cur.rowcount == 0:
                return {"ok": False, "error": "license_not_found"}
        return {"ok": True, "license_key": key, "config_updated": True}

    def list_licenses(self) -> Dict[str, Any]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT l.license_key, l.customer_name, l.phone_vietlott, l.status, l.created_at, l.updated_at, "
                "(SELECT COUNT(*) FROM devices d WHERE d.license_key=l.license_key AND d.active=1) AS active_devices, "
                "(SELECT COUNT(*) FROM rebinds r WHERE r.license_key=l.license_key) AS rebind_count "
                "FROM licenses l ORDER BY l.created_at DESC"
            ).fetchall()
        return {"ok": True, "licenses": [dict(r) for r in rows]}

    def admin_rebind(self, license_key: str, paid_ref: str = "", reason: str = "", admin_note: str = "",
                     fee_vnd: int = REBIND_FEE_VND, force: bool = False) -> Dict[str, Any]:
        key = license_key.upper()
        now = utcnow()
        with self._lock, connect(self.db_path) as conn:
            lic = get_license(conn, key)
            if not lic:
                return {"ok": False, "error": "license_not_found"}
            allowed, why, until = can_rebind_now(conn, key, now)
            if not allowed and not force:
                return {"ok": False, "error": why, "cooldown_until": until,
                        "policy": {"rebind_cooldown_days": REBIND_COOLDOWN_DAYS, "rebind_fee_vnd": REBIND_FEE_VND}}
            active = get_active_device(conn, key)
            old_hash = active["device_id_hash"] if active else None
            if active:
                conn.execute("UPDATE devices SET active=0, revoked_at=? WHERE id=?", (utcnow_iso(), active["id"]))
            cooldown_until = (now + dt.timedelta(days=REBIND_COOLDOWN_DAYS)).replace(microsecond=0).isoformat()
            conn.execute(
                "INSERT INTO rebinds(license_key, old_device_hash, new_device_hash, fee_vnd, paid_ref, reason, admin_note, cooldown_until, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (key, old_hash, None, int(fee_vnd), paid_ref or None, reason or None, admin_note or None, cooldown_until, utcnow_iso()),
            )
            conn.execute("UPDATE licenses SET updated_at=? WHERE license_key=?", (utcnow_iso(), key))
            log_access(conn, key, None, "admin_rebind", True, f"paid_ref={paid_ref} fee={fee_vnd} force={force}")
        return {"ok": True, "license_key": key, "revoked_previous_device": bool(active),
                "fee_vnd": int(fee_vnd), "cooldown_until": cooldown_until,
                "message": "Previous device revoked. Customer may activate the new device now (one active device only)."}

    # ---- client operations ----
    def activate(self, license_key: str, device_id: str, client_info: str = "", ip: str = "") -> Dict[str, Any]:
        key = (license_key or "").strip().upper()
        device_id = (device_id or "").strip()
        if not key or not device_id:
            return {"ok": False, "error": "missing_license_or_device_id"}
        if len(device_id) < 8 or len(device_id) > 200:
            return {"ok": False, "error": "invalid_device_id"}
        with self._lock, connect(self.db_path) as conn:
            lic = get_license(conn, key)
            if not lic:
                log_access(conn, key, device_id, "activate", False, "license_not_found", ip)
                return {"ok": False, "error": "license_not_found"}
            allowed, why = license_allows_access(lic)
            if not allowed:
                log_access(conn, key, device_id, "activate", False, why, ip)
                return {"ok": False, "error": why}

            existing = get_device(conn, key, device_id)
            active = get_active_device(conn, key)

            if existing and existing["active"] == 1:
                conn.execute("UPDATE devices SET last_seen_at=? WHERE id=?", (utcnow_iso(), existing["id"]))
                log_access(conn, key, device_id, "activate", True, "already_active_same_device", ip)
                return {"ok": True, "status": "already_active", "device_bound": True,
                        "message": "This device is already activated for this license.",
                        "policy": {"rebind_fee_vnd": REBIND_FEE_VND, "rebind_cooldown_days": REBIND_COOLDOWN_DAYS}}

            if active and active["device_id_hash"] != sha256_hex(device_id):
                log_access(conn, key, device_id, "activate", False, "another_device_active", ip)
                return {"ok": False, "error": "another_device_active",
                        "message": "License is already bound to another active device. To change device, request support rebind (fee 150,000 VND/change, verification and cooldown apply).",
                        "policy": {"rebind_fee_vnd": REBIND_FEE_VND, "rebind_cooldown_days": REBIND_COOLDOWN_DAYS}}

            # (Re)bind: either no active device, or same device record was revoked and is being reactivated after admin reset
            device_secret = gen_device_secret()
            now = utcnow_iso()
            if existing:
                conn.execute(
                    "UPDATE devices SET device_secret_hash=?, active=1, activated_at=?, revoked_at=NULL, last_seen_at=?, client_info=? WHERE id=?",
                    (sha256_hex(device_secret), now, now, (client_info or "")[:300], existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO devices(license_key, device_id_hash, device_secret_hash, active, activated_at, last_seen_at, client_info) VALUES (?,?,?,?,?,?,?)",
                    (key, sha256_hex(device_id), sha256_hex(device_secret), 1, now, now, (client_info or "")[:300]),
                )
            # mark latest rebind as fulfilled if any pending
            rb = last_rebind(conn, key)
            if rb and not rb["new_device_hash"]:
                conn.execute("UPDATE rebinds SET new_device_hash=? WHERE id=?", (sha256_hex(device_id), rb["id"]))

            conn.execute("UPDATE licenses SET updated_at=? WHERE license_key=?", (now, key))
            log_access(conn, key, device_id, "activate", True, "bound", ip)

        return {
            "ok": True,
            "status": "activated",
            "license_key": key,
            "device_bound": True,
            "device_secret": device_secret,
            "message": "Device activated. Store device_secret securely on this device; it is required to fetch daily plans.",
            "policy": {
                "one_device_only": True,
                "rebind_fee_vnd": REBIND_FEE_VND,
                "rebind_cooldown_days": REBIND_COOLDOWN_DAYS,
            },
        }

    def verify_device(self, conn: sqlite3.Connection, license_key: str, device_id: str, device_secret: str) -> Tuple[bool, str, Optional[sqlite3.Row]]:
        lic = get_license(conn, license_key)
        if not lic:
            return False, "license_not_found", None
        allowed, why = license_allows_access(lic)
        if not allowed:
            return False, why, lic
        dev = get_device(conn, license_key, device_id)
        if not dev or dev["active"] != 1:
            return False, "device_not_active", lic
        expected = dev["device_secret_hash"] or ""
        if not hmac.compare_digest(expected, sha256_hex(device_secret or "")):
            return False, "invalid_device_secret", lic
        # ensure this is the (only) active device
        active = get_active_device(conn, license_key)
        if active and active["id"] != dev["id"]:
            return False, "another_device_active", lic
        return True, "ok", lic

    def today(self, license_key: str, device_id: str, device_secret: str, ip: str = "") -> Dict[str, Any]:
        key = (license_key or "").strip().upper()
        device_id = (device_id or "").strip()
        if not key or not device_id or not device_secret:
            return {"ok": False, "error": "missing_credentials"}
        with self._lock, connect(self.db_path) as conn:
            ok, why, lic = self.verify_device(conn, key, device_id, device_secret)
            if not ok or lic is None:
                log_access(conn, key, device_id, "today", False, why, ip)
                return {"ok": False, "error": why}
            conn.execute("UPDATE devices SET last_seen_at=? WHERE license_key=? AND device_id_hash=?",
                         (utcnow_iso(), key, sha256_hex(device_id)))
            plan = _load_daily_plan_for_today(lic)
            log_access(conn, key, device_id, "today", True, str(plan.get("status", "ok")), ip)
        return {"ok": True, "license_key": key, "plan": plan, "policy": {"bound_device_only": True}}

    def status(self, license_key: str, device_id: str = "", device_secret: str = "", ip: str = "") -> Dict[str, Any]:
        key = (license_key or "").strip().upper()
        with connect(self.db_path) as conn:
            lic = get_license(conn, key)
            if not lic:
                return {"ok": False, "error": "license_not_found"}
            active = get_active_device(conn, key)
            device_ok = False
            if device_id and device_secret:
                v, _, _ = self.verify_device(conn, key, device_id.strip(), device_secret)
                device_ok = v
        return {
            "ok": True,
            "license_key": key,
            "license_status": lic["status"],
            "has_active_device": bool(active),
            "device_authorized": device_ok,
            "policy": {
                "one_device_only": True,
                "rebind_fee_vnd": REBIND_FEE_VND,
                "rebind_cooldown_days": REBIND_COOLDOWN_DAYS,
            },
        }


# ---- HTTP server ----

def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    service: LicenseService = None  # type: ignore
    admin_token: str = ""

    server_version = "VietlottLicenseServer/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # keep concise; avoid leaking secrets
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def _client_ip(self) -> str:
        return (self.headers.get("X-Forwarded-For") or self.client_address[0] or "").split(",")[0].strip()

    def _require_admin(self) -> bool:
        token = self.headers.get("X-Admin-Token", "")
        expected = self.admin_token or os.environ.get(ADMIN_TOKEN_ENV, "")
        return bool(expected) and hmac.compare_digest(token, expected)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query or "")
        svc = self.service

        if path == "/healthz":
            return _json_response(self, 200, {"ok": True, "time": utcnow_iso()})

        if path == "/api/today":
            lic = (qs.get("license_key", [""])[0] or "").strip()
            dev = (qs.get("device_id", [""])[0] or "").strip()
            sec = (qs.get("device_secret", [""])[0] or "").strip()
            res = svc.today(lic, dev, sec, ip=self._client_ip())
            return _json_response(self, 200 if res.get("ok") else 403, res)

        if path == "/api/status":
            lic = (qs.get("license_key", [""])[0] or "").strip()
            dev = (qs.get("device_id", [""])[0] or "").strip()
            sec = (qs.get("device_secret", [""])[0] or "").strip()
            res = svc.status(lic, dev, sec, ip=self._client_ip())
            return _json_response(self, 200 if res.get("ok") else 404, res)

        if path == "/api/admin/licenses":
            if not self._require_admin():
                return _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            return _json_response(self, 200, svc.list_licenses())

        return _json_response(self, 404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = _read_json_body(self)
        svc = self.service
        ip = self._client_ip()

        if path == "/api/activate":
            res = svc.activate(
                body.get("license_key", ""),
                body.get("device_id", ""),
                client_info=str(body.get("client_info", "")),
                ip=ip,
            )
            code = 200 if res.get("ok") else 403
            if res.get("error") == "license_not_found":
                code = 404
            if res.get("error") == "missing_license_or_device_id":
                code = 400
            return _json_response(self, code, res)

        if path == "/api/today":
            res = svc.today(body.get("license_key", ""), body.get("device_id", ""), body.get("device_secret", ""), ip=ip)
            return _json_response(self, 200 if res.get("ok") else 403, res)

        if path == "/api/status":
            res = svc.status(body.get("license_key", ""), body.get("device_id", ""), body.get("device_secret", ""), ip=ip)
            return _json_response(self, 200 if res.get("ok") else 404, res)

        # ---- admin ----
        if path == "/api/admin/create-license":
            if not self._require_admin():
                return _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            try:
                res = svc.create_license(
                    customer_name=str(body.get("customer_name", "")),
                    phone_vietlott=str(body.get("phone_vietlott", "")),
                    notes=str(body.get("notes", "")),
                    license_key=body.get("license_key") or None,
                    config_json=(json.dumps(body.get("config"), ensure_ascii=False) if isinstance(body.get("config"), dict) else body.get("config_json")),
                )
                return _json_response(self, 200, res)
            except sqlite3.IntegrityError:
                return _json_response(self, 409, {"ok": False, "error": "license_already_exists"})

        if path == "/api/admin/set-status":
            if not self._require_admin():
                return _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            res = svc.set_license_status(str(body.get("license_key", "")), str(body.get("status", "")))
            return _json_response(self, 200 if res.get("ok") else 400, res)

        if path == "/api/admin/rebind":
            if not self._require_admin():
                return _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            res = svc.admin_rebind(
                str(body.get("license_key", "")),
                paid_ref=str(body.get("paid_ref", "")),
                reason=str(body.get("reason", "")),
                admin_note=str(body.get("admin_note", "")),
                fee_vnd=int(body.get("fee_vnd", REBIND_FEE_VND)),
                force=bool(body.get("force", False)),
            )
            return _json_response(self, 200 if res.get("ok") else 400, res)

        if path == "/api/admin/set-config":
            if not self._require_admin():
                return _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            cfg = body.get("config") if "config" in body else body.get("config_json")
            res = svc.set_license_config(str(body.get("license_key", "")), cfg)
            return _json_response(self, 200 if res.get("ok") else 400, res)

        return _json_response(self, 404, {"ok": False, "error": "not_found"})


def serve(host: str, port: int, db_path: Path, admin_token: str) -> None:
    svc = LicenseService(db_path)
    Handler.service = svc
    Handler.admin_token = admin_token
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"[license-server] listening on http://{host}:{port} db={db_path}")
    print(f"[license-server] policy: 1 active device/license, rebind {REBIND_FEE_VND} VND, cooldown {REBIND_COOLDOWN_DAYS} days")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


# ---- CLI ----

def main() -> int:
    ap = argparse.ArgumentParser(description="Vietlott Auto Flow - license & delivery server")
    ap.add_argument("--db", dest="db", default=None, help=f"SQLite DB path (default: {DEFAULT_DB} or ${DB_PATH_ENV})")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("serve", help="Run HTTP API server")
    s.add_argument("--host", default=os.environ.get(HOST_ENV, "127.0.0.1"))
    s.add_argument("--port", type=int, default=int(os.environ.get(PORT_ENV, "8787")))
    s.add_argument("--admin-token", default=os.environ.get(ADMIN_TOKEN_ENV, ""))

    c = sub.add_parser("init-db", help="Initialize database")

    c = sub.add_parser("create-license", help="Create a new license")
    c.add_argument("--name", default="")
    c.add_argument("--phone", default="", help="Customer Vietlott SMS phone number")
    c.add_argument("--notes", default="")
    c.add_argument("--key", default="", help="Optional explicit license key")

    c = sub.add_parser("set-status", help="Set license status (active|suspended|revoked|expired)")
    c.add_argument("license_key")
    c.add_argument("status")

    c = sub.add_parser("list", help="List licenses")

    c = sub.add_parser("rebind", help="Approve device change: revoke old device, record fee, enforce cooldown")
    c.add_argument("license_key")
    c.add_argument("--paid-ref", default="", help="Payment reference/transaction id for 150k fee")
    c.add_argument("--reason", default="", help="Reason (lost device/upgrade/reset...)")
    c.add_argument("--admin-note", default="")
    c.add_argument("--fee", type=int, default=REBIND_FEE_VND)
    c.add_argument("--force", action="store_true", help="Override cooldown (use with caution, logged)")

    c = sub.add_parser("set-config", help="Set per-customer config JSON (game/mode/ticket_count/custom_tickets)")
    c.add_argument("license_key")
    c.add_argument("--config", default=None, help="JSON string config")
    c.add_argument("--config-file", default=None, help="Path to JSON config file")

    c = sub.add_parser("show-policy", help="Print enforced policy")

    args = ap.parse_args()
    db_path = get_db_path(args.db)

    if args.cmd in (None, "show-policy"):
        print(json.dumps({
            "max_active_devices_per_license": MAX_ACTIVE_DEVICES_PER_LICENSE,
            "rebind_fee_vnd": REBIND_FEE_VND,
            "rebind_cooldown_days": REBIND_COOLDOWN_DAYS,
            "db_path": str(db_path),
        }, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "serve":
        serve(args.host, args.port, db_path, args.admin_token or os.environ.get(ADMIN_TOKEN_ENV, ""))
        return 0

    if args.cmd == "init-db":
        init_db(db_path)
        print(f"initialized {db_path}")
        return 0

    svc = LicenseService(db_path)

    if args.cmd == "create-license":
        res = svc.create_license(customer_name=args.name, phone_vietlott=args.phone, notes=args.notes, license_key=(args.key or None))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if args.cmd == "set-status":
        res = svc.set_license_status(args.license_key, args.status)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if args.cmd == "list":
        res = svc.list_licenses()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "rebind":
        res = svc.admin_rebind(args.license_key, paid_ref=args.paid_ref, reason=args.reason, admin_note=args.admin_note, fee_vnd=args.fee, force=args.force)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if args.cmd == "set-config":
        cfg_obj = None
        if args.config_file:
            try:
                cfg_obj = json.loads(Path(args.config_file).read_text(encoding="utf-8"))
            except Exception as exc:
                print(json.dumps({"ok": False, "error": f"invalid_config_file: {exc}"}, ensure_ascii=False))
                return 1
        if args.config is not None:
            try:
                cfg_obj = json.loads(args.config)
            except Exception as exc:
                print(json.dumps({"ok": False, "error": f"invalid_config_json: {exc}"}, ensure_ascii=False))
                return 1
        res = svc.set_license_config(args.license_key, cfg_obj)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
