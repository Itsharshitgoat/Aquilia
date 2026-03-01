"""
AquilAdmin — Admin User ORM Model.

Stores superuser and staff credentials in the database via Aquilia's ORM,
replacing the legacy .env-based approach.  Follows Django's architecture:

    - ``AdminUser`` model with ``is_superuser`` / ``is_staff`` flags
    - Password hashing via ``PasswordHasher`` (Argon2id / PBKDF2 fallback)
    - ``createsuperuser`` writes to the DB, not a flat file
    - ``aq db migrate`` creates the admin_users table automatically

Usage::

    from aquilia.admin.models import AdminUser

    # Create a superuser (CLI does this via ``aq admin createsuperuser``)
    user = await AdminUser.create_superuser(
        username="admin",
        password="s3cret",
        email="admin@example.com",
    )

    # Authenticate
    user = await AdminUser.authenticate("admin", "s3cret")
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Type

# ── Lightweight field stubs used when the full ORM is not wired ──────────────
# In a real workspace the concrete ORM fields are imported, but during
# unit-tests the admin module must remain importable without a live DB
# connection.  We therefore define a tiny shim layer that the full ORM
# metaclass picks up if available.

try:
    from aquilia.models.base import Model
    from aquilia.models.fields_module import (
        CharField,
        EmailField,
        BooleanField,
        DateTimeField,
        AutoField,
        TextField,
    )
    _HAS_ORM = True
except Exception:  # pragma: no cover
    _HAS_ORM = False

# ── Password hashing helpers ────────────────────────────────────────────────

try:
    from aquilia.auth.hashing import PasswordHasher as _PH
    _hasher = _PH()
except Exception:
    _hasher = None  # type: ignore[assignment]


def _hash_password(raw_password: str) -> str:
    """Hash a raw password using the best available algorithm."""
    if _hasher is not None:
        return _hasher.hash(raw_password)
    # Minimal fallback using PBKDF2-SHA256
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), 600_000)
    return f"$pbkdf2_sha256$600000${salt}${dk.hex()}"


def _verify_password(password_hash: str, raw_password: str) -> bool:
    """Verify a raw password against a stored hash."""
    if _hasher is not None:
        return _hasher.verify(password_hash, raw_password)
    # Minimal fallback
    if not password_hash.startswith("$pbkdf2_sha256$"):
        return False
    parts = password_hash.split("$")
    if len(parts) != 5:
        return False
    iterations = int(parts[2])
    salt = parts[3]
    expected_hash = parts[4]
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), iterations)
    return dk.hex() == expected_hash


# ── AdminUser model ─────────────────────────────────────────────────────────

if _HAS_ORM:
    class AdminUser(Model):
        """
        Admin user stored in the database.

        Replaces the old ``.env``-based superuser mechanism.
        Created via ``aq admin createsuperuser`` which calls
        ``AdminUser.create_superuser(...)``.
        """

        table = "admin_users"

        username = CharField(max_length=150, unique=True)
        email = EmailField(max_length=254, blank=True, default="")
        password_hash = TextField()
        is_superuser = BooleanField(default=False)
        is_staff = BooleanField(default=True)
        is_active = BooleanField(default=True)
        first_name = CharField(max_length=150, blank=True, default="")
        last_name = CharField(max_length=150, blank=True, default="")
        last_login = DateTimeField(null=True, blank=True)
        date_joined = DateTimeField(auto_now_add=True)

        class Meta:
            ordering = ["-date_joined"]
            verbose_name = "Admin User"
            verbose_name_plural = "Admin Users"
            get_latest_by = "date_joined"

        # ── Helpers ──────────────────────────────────────────────────

        def __str__(self) -> str:
            return self.username or repr(self)

        def set_password(self, raw_password: str) -> None:
            """Hash and set a new password (in-memory, call .save())."""
            self.password_hash = _hash_password(raw_password)

        def check_password(self, raw_password: str) -> bool:
            """Verify ``raw_password`` against the stored hash."""
            return _verify_password(self.password_hash, raw_password)

        def get_full_name(self) -> str:
            parts = [
                getattr(self, "first_name", "") or "",
                getattr(self, "last_name", "") or "",
            ]
            return " ".join(p for p in parts if p).strip() or self.username

        def to_identity(self) -> "Identity":
            """Convert to an ``Identity`` object for the auth subsystem."""
            from aquilia.auth.core import Identity, IdentityType, IdentityStatus

            roles: list[str] = []
            if getattr(self, "is_superuser", False):
                roles.append("superadmin")
            if getattr(self, "is_staff", False):
                roles.append("staff")

            return Identity(
                id=str(self.pk),
                type=IdentityType.USER,
                attributes={
                    "name": self.get_full_name(),
                    "username": self.username,
                    "email": getattr(self, "email", ""),
                    "roles": roles,
                    "is_superuser": getattr(self, "is_superuser", False),
                    "is_staff": getattr(self, "is_staff", False),
                    "admin_role": "superadmin" if getattr(self, "is_superuser", False) else "staff",
                },
                status=IdentityStatus.ACTIVE if getattr(self, "is_active", True) else IdentityStatus.SUSPENDED,
            )

        # ── Class-level factory methods ──────────────────────────────

        @classmethod
        async def create_superuser(
            cls,
            username: str,
            password: str,
            email: str = "",
            **extra_fields: Any,
        ) -> "AdminUser":
            """Create a superuser record in the database."""
            hashed = _hash_password(password)
            return await cls.create(
                username=username,
                email=email,
                password_hash=hashed,
                is_superuser=True,
                is_staff=True,
                is_active=True,
                **extra_fields,
            )

        @classmethod
        async def create_staff_user(
            cls,
            username: str,
            password: str,
            email: str = "",
            **extra_fields: Any,
        ) -> "AdminUser":
            """Create a staff (non-super) user."""
            hashed = _hash_password(password)
            return await cls.create(
                username=username,
                email=email,
                password_hash=hashed,
                is_superuser=False,
                is_staff=True,
                is_active=True,
                **extra_fields,
            )

        @classmethod
        async def authenticate(
            cls,
            username: str,
            password: str,
        ) -> Optional["AdminUser"]:
            """
            Authenticate by username + password.

            Returns the ``AdminUser`` instance on success, ``None`` on failure.
            """
            try:
                user = await cls.objects.get(username=username)
            except Exception:
                return None

            if user is None:
                return None

            if not getattr(user, "is_active", True):
                return None

            if not _verify_password(user.password_hash, password):
                return None

            # Update last_login
            try:
                await cls.objects.filter(pk=user.pk).update(
                    {"last_login": datetime.now(timezone.utc)}
                )
            except Exception:
                pass  # Non-critical

            return user

else:
    # Fallback when ORM is not available — provides the same public API
    # via a plain dataclass so that imports never crash.
    class AdminUser:  # type: ignore[no-redef]
        """Stub AdminUser when ORM fields are not available."""

        _HAS_ORM = False

        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def check_password(self, raw_password: str) -> bool:
            return _verify_password(getattr(self, "password_hash", ""), raw_password)

        def set_password(self, raw_password: str) -> None:
            self.password_hash = _hash_password(raw_password)

        def to_identity(self):  # type: ignore[return]
            from aquilia.auth.core import Identity, IdentityType, IdentityStatus
            roles: list[str] = []
            if getattr(self, "is_superuser", False):
                roles.append("superadmin")
            if getattr(self, "is_staff", False):
                roles.append("staff")
            return Identity(
                id=str(getattr(self, "pk", "stub")),
                type=IdentityType.USER,
                attributes={
                    "name": getattr(self, "username", "admin"),
                    "username": getattr(self, "username", "admin"),
                    "roles": roles,
                    "is_superuser": getattr(self, "is_superuser", False),
                    "is_staff": getattr(self, "is_staff", False),
                    "admin_role": "superadmin" if getattr(self, "is_superuser", False) else "staff",
                },
                status=IdentityStatus.ACTIVE,
            )

        @classmethod
        async def authenticate(cls, username: str, password: str) -> Optional["AdminUser"]:
            return None

        @classmethod
        async def create_superuser(cls, username: str, password: str, email: str = "", **kw: Any) -> "AdminUser":
            raise RuntimeError("ORM not available — cannot create superuser without database models")

        def get_full_name(self) -> str:
            return getattr(self, "username", "admin")


# ── Exported helpers ────────────────────────────────────────────────────────

__all__ = [
    "AdminUser",
    "_hash_password",
    "_verify_password",
]
