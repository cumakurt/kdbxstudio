"""Core package exports."""

from kdbxstudio.core.cache import Cache, EntryIndexCache
from kdbxstudio.core.crypto import SecureString, wipe_bytearray, wipe_bytes
from kdbxstudio.core.database import (
    AttachmentView,
    DatabaseError,
    DatabaseNotOpenError,
    EntryView,
    GroupView,
    HistoryView,
    InvalidCredentialsError,
    KdbxDatabase,
    redact_entry_secrets,
)
from kdbxstudio.core.password_generator import (
    GeneratorOptions,
    generate_password,
)
from kdbxstudio.core.pem_inspector import PemBlockInfo, inspect_pem_text

__all__ = [
    "AttachmentView",
    "Cache",
    "DatabaseError",
    "DatabaseNotOpenError",
    "EntryIndexCache",
    "EntryView",
    "GeneratorOptions",
    "GroupView",
    "HistoryView",
    "InvalidCredentialsError",
    "KdbxDatabase",
    "PemBlockInfo",
    "SecureString",
    "generate_password",
    "inspect_pem_text",
    "redact_entry_secrets",
    "wipe_bytearray",
    "wipe_bytes",
]
