"""Security package."""

from kdbxstudio.security.session import AutoLockController, ClipboardGuard
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import (
    clear_recent_databases,
    load_recent_databases,
    load_settings,
    remember_database,
    save_settings,
)

__all__ = [
    "AutoLockController",
    "ClipboardGuard",
    "SecuritySettings",
    "clear_recent_databases",
    "load_recent_databases",
    "load_settings",
    "remember_database",
    "save_settings",
]
