"""Authentication + multi-tenant identity.

Industries are the tenants; every user belongs to exactly one industry, and
each industry gets its own knowledge graph, documents and query history.

Same resilience contract as the LLM (llm.py) and persistence (persistence.py)
layers: the in-memory registry is the session's source of truth — the demo
account below ALWAYS works, even fully offline — and Supabase is a mirror:
hydrated at boot, written through on signup, so accounts survive restarts
whenever it's reachable. If it isn't, signup still works for the session.

No new dependencies: passwords are PBKDF2-HMAC-SHA256 (hashlib), tokens are
HMAC-SHA256-signed JSON (JWT-shaped, hmac + base64).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

from . import config
from .persistence import get_store

# The always-available demo tenant: pre-seeded corpus, credentials shown on
# the login page so anyone can explore immediately.
DEMO_INDUSTRY_ID = "demo"
DEMO_INDUSTRY_NAME = "Demo Refinery"
DEMO_EMAIL = "demo@industryiq.app"
DEMO_PASSWORD = "demo123"

_PBKDF2_ITERS = 120_000


# --------------------------------------------------------------------------- #
# Passwords + tokens (stdlib only)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERS)
    return f"pbkdf2${_PBKDF2_ITERS}${salt}${dk.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, want = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(dk.hex(), want)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_token(payload: dict) -> str:
    body = _b64(json.dumps({**payload, "exp": int(time.time()) + config.TOKEN_TTL_S},
                           separators=(",", ":")).encode())
    sig = _b64(hmac.new(config.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token: str) -> Optional[dict]:
    """Return the token's payload if the signature and expiry check out."""
    try:
        body, sig = token.split(".")
        want = _b64(hmac.new(config.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, want):
            return None
        payload = json.loads(_unb64(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
@dataclass
class Industry:
    id: str
    name: str
    join_code: str


@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str
    industry_id: str
    role: str = "member"


class AuthError(Exception):
    """User-facing auth failure (bad credentials, duplicate email, bad code)."""


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "industry"


class AuthRegistry:
    def __init__(self) -> None:
        self._store = get_store()
        self._lock = threading.Lock()
        self._industries: dict[str, Industry] = {}
        self._users: dict[str, User] = {}          # keyed by lowercase email
        self._seed_demo()
        self._hydrate()

    def _seed_demo(self) -> None:
        self._industries[DEMO_INDUSTRY_ID] = Industry(
            id=DEMO_INDUSTRY_ID, name=DEMO_INDUSTRY_NAME, join_code="DEMO-0000")
        self._users[DEMO_EMAIL] = User(
            id="demo-user", email=DEMO_EMAIL, name="Demo Engineer",
            password_hash=hash_password(DEMO_PASSWORD),
            industry_id=DEMO_INDUSTRY_ID, role="admin")

    def _hydrate(self) -> None:
        """Best-effort restore of industries/users from the persistence store."""
        try:
            for r in self._store.load_industries():
                if r.get("id") and r["id"] != DEMO_INDUSTRY_ID:
                    self._industries[r["id"]] = Industry(
                        id=r["id"], name=r.get("name", r["id"]),
                        join_code=r.get("join_code", ""))
            n = 0
            for r in self._store.load_users():
                email = (r.get("email") or "").lower()
                if email and email != DEMO_EMAIL:
                    self._users[email] = User(
                        id=r.get("id") or email, email=email,
                        name=r.get("name", email),
                        password_hash=r.get("password_hash", ""),
                        industry_id=r.get("industry_id", DEMO_INDUSTRY_ID),
                        role=r.get("role", "member"))
                    n += 1
            if n:
                print(f"[auth] restored {len(self._industries) - 1} industrie(s) / {n} user(s)")
        except Exception as exc:
            print(f"[auth] hydrate failed ({exc}); starting with demo account only")

    # ------------------------------------------------------------------ #
    def _principal(self, u: User) -> dict:
        ind = self._industries.get(u.industry_id)
        return {
            "uid": u.id, "email": u.email, "name": u.name, "role": u.role,
            "iid": u.industry_id,
            "industry": ind.name if ind else u.industry_id,
            "join_code": ind.join_code if ind else "",
        }

    def login(self, email: str, password: str) -> dict:
        u = self._users.get((email or "").strip().lower())
        if not u or not check_password(password or "", u.password_hash):
            raise AuthError("Invalid email or password.")
        return self._principal(u)

    def register(self, email: str, name: str, password: str,
                 industry_name: str = "", join_code: str = "") -> dict:
        """Create a user — either founding a new industry (industry_name) or
        joining an existing one (join_code). Exactly one must be provided."""
        email = (email or "").strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise AuthError("Please enter a valid email address.")
        if len(password or "") < 6:
            raise AuthError("Password must be at least 6 characters.")
        if not (name or "").strip():
            raise AuthError("Please enter your name.")

        with self._lock:
            if email in self._users:
                raise AuthError("An account with this email already exists — sign in instead.")

            if industry_name.strip():
                ind = self._create_industry(industry_name.strip())
                role = "admin"
            elif join_code.strip():
                ind = self._by_join_code(join_code.strip())
                if not ind:
                    raise AuthError("Unknown invite code — check it with your industry admin.")
                role = "member"
            else:
                raise AuthError("Provide an industry name (create) or an invite code (join).")

            u = User(id=secrets.token_hex(8), email=email, name=name.strip(),
                     password_hash=hash_password(password),
                     industry_id=ind.id, role=role)
            self._users[email] = u

        # mirror to Supabase (best-effort; store swallows failures)
        self._store.save_industry(asdict(ind))
        self._store.save_user(asdict(u))
        return self._principal(u)

    def _create_industry(self, name: str) -> Industry:
        norm = name.strip().lower()
        for ind in self._industries.values():
            if ind.name.strip().lower() == norm:
                raise AuthError(f"'{name}' already exists — ask its admin for the invite code.")
        base = _slug(name)
        iid = base
        while iid in self._industries:
            iid = f"{base}-{secrets.token_hex(2)}"
        code = f"{base[:4].upper()}-{secrets.token_hex(2).upper()}"
        ind = Industry(id=iid, name=name, join_code=code)
        self._industries[iid] = ind
        return ind

    def _by_join_code(self, code: str) -> Optional[Industry]:
        for ind in self._industries.values():
            if hmac.compare_digest(ind.join_code.lower(), code.lower()):
                return ind
        return None

    def industry(self, iid: str) -> Optional[Industry]:
        return self._industries.get(iid)


# --------------------------------------------------------------------------- #
# Singleton
# --------------------------------------------------------------------------- #
_REGISTRY: Optional[AuthRegistry] = None
_REG_LOCK = threading.Lock()


def get_auth() -> AuthRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        with _REG_LOCK:
            if _REGISTRY is None:
                _REGISTRY = AuthRegistry()
    return _REGISTRY
