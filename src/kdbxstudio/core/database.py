"""KDBX database wrapper around pykeepass."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pykeepass import PyKeePass, create_database
from pykeepass.exceptions import CredentialsError
from pykeepass.group import Group

from kdbxstudio.core.crypto import SecureString


class DatabaseError(Exception):
    """Base error for database operations."""


class InvalidCredentialsError(DatabaseError):
    """Raised when password / key file credentials are wrong."""


class DatabaseNotOpenError(DatabaseError):
    """Raised when an operation requires an open database."""


@dataclass(frozen=True)
class EntryView:
    """Immutable snapshot of an entry for UI / search layers."""

    uuid: str
    title: str
    username: str
    password: str
    url: str
    notes: str
    group_path: str
    custom_properties: dict[str, str] = field(default_factory=dict)
    in_recycle_bin: bool = False
    otp: str = ""
    expires: bool = False
    expiry_time: str = ""
    tags: tuple[str, ...] = ()
    attachment_count: int = 0


@dataclass(frozen=True)
class GroupView:
    """Immutable snapshot of a group."""

    uuid: str
    name: str
    path: str
    parent_uuid: str | None
    is_recycle_bin: bool = False


@dataclass(frozen=True)
class HistoryView:
    """Snapshot of a historical entry revision."""

    index: int
    title: str
    username: str
    password: str
    url: str
    notes: str
    modified: str
    otp: str = ""
    tags: tuple[str, ...] = ()
    custom_properties: dict[str, str] = field(default_factory=dict)
    expires: bool = False
    expiry_time: str = ""


@dataclass(frozen=True)
class AttachmentView:
    """Attachment metadata (+ optional inline bytes for preview)."""

    id: int
    filename: str
    size: int
    data: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class DatabaseInfo:
    """High-level database metadata for the properties dialog."""

    path: str
    entry_count: int
    group_count: int
    recycle_bin_entries: int
    dirty: bool
    version: str
    kdf_algorithm: str = "unknown"
    encryption: str = "unknown"


class KdbxDatabase:
    """Thin wrapper over pykeepass with open/save/create helpers."""

    def __init__(self) -> None:
        self._kp: PyKeePass | None = None
        self._path: Path | None = None
        self._password: SecureString | None = None
        self._keyfile: Path | None = None
        self._dirty = False
        self._entry_by_uuid: dict[str, Any] | None = None
        self._group_by_uuid: dict[str, Group] | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def is_open(self) -> bool:
        return self._kp is not None

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def create(
        self,
        path: Path | str,
        password: str | None = None,
        keyfile: Path | str | None = None,
    ) -> None:
        """Create a new empty KDBX database and open it."""
        self.close()
        path = Path(path)
        keyfile_path = Path(keyfile) if keyfile else None
        create_database(
            str(path),
            password=password,
            keyfile=str(keyfile_path) if keyfile_path else None,
        )
        self.open(path, password=password, keyfile=keyfile_path)

    def open(
        self,
        path: Path | str,
        password: str | None = None,
        keyfile: Path | str | None = None,
    ) -> None:
        """Open an existing KDBX database."""
        self.close()
        path = Path(path)
        keyfile_path = Path(keyfile) if keyfile else None
        try:
            self._kp = PyKeePass(
                str(path),
                password=password,
                keyfile=str(keyfile_path) if keyfile_path else None,
            )
        except CredentialsError as exc:
            raise InvalidCredentialsError("Invalid password or key file") from exc
        except Exception as exc:
            raise DatabaseError(f"Failed to open database: {exc}") from exc
        self._path = path
        self._set_password(password)
        self._keyfile = keyfile_path
        self._dirty = False
        self._invalidate_indexes()

    def save(self, path: Path | str | None = None) -> None:
        """Save the database to disk."""
        kp = self._require_kp()
        if path is not None:
            self._path = Path(path)
            kp.filename = str(self._path)
        if self._path is None:
            raise DatabaseError("No path set for save")
        if self._password is not None:
            kp.password = self._password.get()
        try:
            kp.save()
        except Exception as exc:
            raise DatabaseError(f"Failed to save database: {exc}") from exc
        self._dirty = False

    def close(self) -> None:
        """Close the database and clear credentials from this wrapper."""
        if self._kp is not None:
            try:
                self._kp.password = None
            except Exception:
                pass
            try:
                self._kp.keyfile = None
            except Exception:
                pass
        self._kp = None
        self._path = None
        self._clear_password()
        self._keyfile = None
        self._dirty = False
        self._invalidate_indexes()

    def _set_password(self, password: str | None) -> None:
        self._clear_password()
        if password:
            self._password = SecureString(password)

    def _clear_password(self) -> None:
        if self._password is not None:
            self._password.wipe()
            self._password = None

    def list_groups(self) -> list[GroupView]:
        kp = self._require_kp()
        recycle_uuid = self._recycle_bin_uuid()
        result: list[GroupView] = []
        for group in kp.groups:
            parent = group.parentgroup
            uuid = str(group.uuid)
            result.append(
                GroupView(
                    uuid=uuid,
                    name=group.name or "",
                    path=self._group_path(group),
                    parent_uuid=str(parent.uuid) if parent is not None else None,
                    is_recycle_bin=uuid == recycle_uuid,
                )
            )
        return result

    def add_group(self, parent_uuid: str, name: str) -> GroupView:
        kp = self._require_kp()
        parent = self._find_group(parent_uuid)
        group = kp.add_group(parent, name)
        self._dirty = True
        self._invalidate_indexes()
        recycle_uuid = self._recycle_bin_uuid()
        parent_group = group.parentgroup
        return GroupView(
            uuid=str(group.uuid),
            name=group.name or "",
            path=self._group_path(group),
            parent_uuid=str(parent_group.uuid) if parent_group is not None else None,
            is_recycle_bin=str(group.uuid) == recycle_uuid,
        )

    def rename_group(self, group_uuid: str, name: str) -> GroupView:
        group = self._find_group(group_uuid)
        if not name.strip():
            raise DatabaseError("Group name cannot be empty")
        if self._recycle_bin_uuid() == group_uuid:
            raise DatabaseError("Cannot rename the Recycle Bin")
        if str(self.root_group_uuid()) == group_uuid:
            # Root rename is allowed in KeePass but unusual; still permit
            pass
        group.name = name.strip()
        self._dirty = True
        parent = group.parentgroup
        return GroupView(
            uuid=str(group.uuid),
            name=group.name or "",
            path=self._group_path(group),
            parent_uuid=str(parent.uuid) if parent is not None else None,
            is_recycle_bin=False,
        )

    def delete_group(self, group_uuid: str, *, permanent: bool = False) -> None:
        kp = self._require_kp()
        if group_uuid == self.root_group_uuid():
            raise DatabaseError("Cannot delete the root group")
        if group_uuid == self._recycle_bin_uuid():
            raise DatabaseError("Cannot delete the Recycle Bin group")
        group = self._find_group(group_uuid)
        if permanent:
            kp.delete_group(group)
        else:
            kp.trash_group(group)
        self._dirty = True
        self._invalidate_indexes()

    def ensure_group_path(self, path: str) -> str:
        """Create nested groups from a path like Root/Work/Dev; return leaf UUID."""
        kp = self._require_kp()
        parts = [p for p in path.replace("\\", "/").split("/") if p.strip()]
        # Skip leading "Root" if present (matches KeePass path style)
        if parts and parts[0].lower() in {"root", (kp.root_group.name or "").lower()}:
            parts = parts[1:]
        current = kp.root_group
        for part in parts:
            child = None
            for group in current.subgroups:
                if (group.name or "") == part:
                    child = group
                    break
            if child is None:
                child = kp.add_group(current, part)
                self._dirty = True
                self._invalidate_indexes()
            current = child
        return str(current.uuid)

    def change_credentials(
        self,
        *,
        password: str | None = None,
        keyfile: Path | str | None = None,
        clear_keyfile: bool = False,
    ) -> None:
        """Update master password and/or key file used for the next save."""
        self._require_kp()
        if password is not None:
            self._set_password(password)
            self._kp.password = password  # type: ignore[union-attr]
        if clear_keyfile:
            self._keyfile = None
            self._kp.keyfile = None  # type: ignore[union-attr]
        elif keyfile is not None:
            key_path = Path(keyfile)
            self._keyfile = key_path
            self._kp.keyfile = str(key_path)  # type: ignore[union-attr]
        self._dirty = True

    def list_entries(
        self,
        group_uuid: str | None = None,
        *,
        include_recycle_bin: bool = True,
    ) -> list[EntryView]:
        kp = self._require_kp()
        entries = kp.entries
        if group_uuid is not None:
            group = self._find_group(group_uuid)
            entries = group.entries
        recycle_uuid = self._recycle_bin_uuid()
        path_cache: dict[str, str] = {}
        views = [
            self._to_entry_view(
                entry, recycle_uuid=recycle_uuid, path_cache=path_cache
            )
            for entry in entries
        ]
        if not include_recycle_bin and group_uuid is None:
            views = [e for e in views if not e.in_recycle_bin]
        return views

    def get_entry(self, entry_uuid: str) -> EntryView | None:
        try:
            entry = self._find_entry(entry_uuid)
        except DatabaseError:
            return None
        return self._to_entry_view(entry)

    def add_entry(
        self,
        group_uuid: str,
        title: str,
        username: str = "",
        password: str = "",
        url: str = "",
        notes: str = "",
        custom_properties: dict[str, str] | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
        expires: bool | None = None,
        expiry_time: datetime | None = None,
    ) -> EntryView:
        kp = self._require_kp()
        group = self._find_group(group_uuid)
        entry = kp.add_entry(
            group,
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            tags=list(tags) if tags else None,
            expiry_time=expiry_time,
        )
        if expires is not None:
            entry.expires = expires
        if custom_properties:
            for key, value in custom_properties.items():
                entry.set_custom_property(key, value)
        self._dirty = True
        self._invalidate_indexes()
        return self._to_entry_view(entry)

    def update_entry(
        self,
        entry_uuid: str,
        *,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
        notes: str | None = None,
        otp: str | None = None,
        custom_properties: dict[str, str] | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
        expires: bool | None = None,
        expiry_time: datetime | None = None,
        keep_history: bool = True,
    ) -> EntryView:
        entry = self._find_entry(entry_uuid)
        if keep_history:
            entry.save_history()
        if title is not None:
            entry.title = title
        if username is not None:
            entry.username = username
        if password is not None:
            entry.password = password
        if url is not None:
            entry.url = url
        if notes is not None:
            entry.notes = notes
        if otp is not None:
            entry.otp = otp
        if tags is not None:
            entry.tags = list(tags)
        if expiry_time is not None:
            entry.expiry_time = expiry_time
        if expires is not None:
            entry.expires = expires
        elif expiry_time is not None:
            entry.expires = True
        if custom_properties is not None:
            existing = dict(entry.custom_properties or {})
            for key in list(existing):
                if key not in custom_properties:
                    entry.delete_custom_property(key)
            for key, value in custom_properties.items():
                entry.set_custom_property(key, value)
        self._dirty = True
        return self._to_entry_view(entry)

    def move_entry(self, entry_uuid: str, group_uuid: str) -> EntryView:
        kp = self._require_kp()
        entry = self._find_entry(entry_uuid)
        group = self._find_group(group_uuid)
        kp.move_entry(entry, group)
        self._dirty = True
        self._invalidate_indexes()
        return self._to_entry_view(entry)

    def list_history(self, entry_uuid: str) -> list[HistoryView]:
        entry = self._find_entry(entry_uuid)
        history = list(entry.history or [])
        result: list[HistoryView] = []
        for index, item in enumerate(reversed(history)):
            modified = ""
            mtime = getattr(item, "mtime", None)
            if mtime is not None:
                modified = str(mtime)
            tags_raw = getattr(item, "tags", None) or []
            tags = tuple(str(t).strip() for t in tags_raw if str(t).strip())
            props = {
                str(k): str(v)
                for k, v in dict(getattr(item, "custom_properties", None) or {}).items()
            }
            expiry = ""
            expires = bool(getattr(item, "expires", False))
            expiry_time = getattr(item, "expiry_time", None)
            if expiry_time is not None:
                try:
                    expiry = expiry_time.isoformat()
                except Exception:
                    expiry = str(expiry_time)
            result.append(
                HistoryView(
                    index=index,
                    title=item.title or "",
                    username=item.username or "",
                    password=item.password or "",
                    url=item.url or "",
                    notes=item.notes or "",
                    modified=modified,
                    otp=item.otp or "",
                    tags=tags,
                    custom_properties=props,
                    expires=expires,
                    expiry_time=expiry,
                )
            )
        return result

    def restore_history(self, entry_uuid: str, history_index: int) -> EntryView:
        """Restore a history revision (0 = most recent historical snapshot)."""
        kp = self._require_kp()
        entry = self._find_entry(entry_uuid)
        history = list(entry.history or [])
        if not history:
            raise DatabaseError("Entry has no history")
        # UI index 0 is the newest historical item (last in pykeepass list)
        try:
            snapshot = history[-(history_index + 1)]
        except IndexError as exc:
            raise DatabaseError(f"Invalid history index: {history_index}") from exc
        entry.save_history()
        entry.title = snapshot.title or ""
        entry.username = snapshot.username or ""
        entry.password = snapshot.password or ""
        entry.url = snapshot.url or ""
        entry.notes = snapshot.notes or ""
        entry.otp = snapshot.otp or ""
        tags_raw = getattr(snapshot, "tags", None) or []
        entry.tags = [str(t) for t in tags_raw]
        entry.expires = bool(getattr(snapshot, "expires", False))
        expiry_time = getattr(snapshot, "expiry_time", None)
        if expiry_time is not None:
            entry.expiry_time = expiry_time
        snap_props = {
            str(k): str(v)
            for k, v in dict(getattr(snapshot, "custom_properties", None) or {}).items()
        }
        existing = dict(entry.custom_properties or {})
        for key in list(existing):
            if key not in snap_props:
                entry.delete_custom_property(key)
        for key, value in snap_props.items():
            entry.set_custom_property(key, value)
        for attachment in list(entry.attachments or []):
            attachment.delete()
        for attachment in list(getattr(snapshot, "attachments", None) or []):
            data = bytes(attachment.binary or b"")
            filename = Path(str(attachment.filename or "attachment")).name
            if not filename or filename in {".", ".."}:
                filename = "attachment"
            binary_id = kp.add_binary(data)
            entry.add_attachment(binary_id, filename)
        self._dirty = True
        self._invalidate_indexes()
        return self._to_entry_view(entry)

    def database_info(self) -> DatabaseInfo:
        kp = self._require_kp()
        recycle_count = sum(
            1 for entry in kp.entries if self._is_in_recycle_bin(entry)
        )
        version = "unknown"
        try:
            version = f"{kp.version[0]}.{kp.version[1]}"
        except Exception:
            pass
        kdf = "unknown"
        try:
            kdf = str(getattr(kp, "kdf_algorithm", None) or "unknown")
        except Exception:
            pass
        encryption = "AES / ChaCha20 (KeePass)"
        try:
            enc = getattr(kp, "encryption_algorithm", None)
            if enc:
                encryption = str(enc)
        except Exception:
            pass
        return DatabaseInfo(
            path=str(self._path) if self._path else "",
            entry_count=len(kp.entries),
            group_count=len(kp.groups),
            recycle_bin_entries=recycle_count,
            dirty=self._dirty,
            version=version,
            kdf_algorithm=kdf,
            encryption=encryption,
        )

    def list_attachments(
        self,
        entry_uuid: str,
        *,
        include_data: bool = False,
    ) -> list[AttachmentView]:
        """List attachments. Binary payloads are omitted unless ``include_data``."""
        entry = self._find_entry(entry_uuid)
        result: list[AttachmentView] = []
        for attachment in entry.attachments or []:
            raw = attachment.binary or b""
            size = len(raw)
            data = bytes(raw) if include_data else b""
            result.append(
                AttachmentView(
                    id=int(attachment.id),
                    filename=str(attachment.filename or ""),
                    size=size,
                    data=data,
                )
            )
        return result

    def get_attachment_data(self, entry_uuid: str, attachment_id: int) -> bytes:
        """Load a single attachment payload by id."""
        entry = self._find_entry(entry_uuid)
        for attachment in entry.attachments or []:
            if int(attachment.id) == attachment_id:
                return bytes(attachment.binary or b"")
        raise DatabaseError(f"Attachment not found: {attachment_id}")

    def attachment_count(self, entry_uuid: str) -> int:
        """Count attachments without copying binary payloads into memory."""
        entry = self._find_entry(entry_uuid)
        return len(entry.attachments or [])

    def add_attachment(
        self, entry_uuid: str, filename: str, data: bytes
    ) -> AttachmentView:
        kp = self._require_kp()
        entry = self._find_entry(entry_uuid)
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise DatabaseError("Invalid attachment filename")
        binary_id = kp.add_binary(data)
        attachment = entry.add_attachment(binary_id, safe_name)
        self._dirty = True
        self._invalidate_indexes()
        payload = bytes(attachment.binary or b"")
        return AttachmentView(
            id=int(attachment.id),
            filename=str(attachment.filename or safe_name),
            size=len(payload),
            data=payload,
        )

    def delete_attachment(self, entry_uuid: str, attachment_id: int) -> None:
        entry = self._find_entry(entry_uuid)
        for attachment in list(entry.attachments or []):
            if int(attachment.id) == attachment_id:
                attachment.delete()
                self._dirty = True
                self._invalidate_indexes()
                return
        raise DatabaseError(f"Attachment not found: {attachment_id}")

    def trash_entry(self, entry_uuid: str) -> None:
        """Move an entry to the Recycle Bin."""
        kp = self._require_kp()
        entry = self._find_entry(entry_uuid)
        kp.trash_entry(entry)
        self._dirty = True
        self._invalidate_indexes()

    def delete_entry(self, entry_uuid: str, *, permanent: bool = False) -> None:
        """Trash by default; permanently delete when requested."""
        if permanent:
            kp = self._require_kp()
            entry = self._find_entry(entry_uuid)
            kp.delete_entry(entry)
            self._dirty = True
            self._invalidate_indexes()
            return
        self.trash_entry(entry_uuid)

    def empty_recycle_bin(self) -> int:
        """Permanently delete all entries and subgroups in the Recycle Bin.

        Trashed groups land as subgroups under the bin, so deleting only
        ``recycle.entries`` leaves nested secrets behind.
        """
        kp = self._require_kp()
        recycle = kp.recyclebin_group
        if recycle is None:
            return 0

        def _collect_entries(group: Group) -> list[Any]:
            found: list[Any] = list(group.entries or [])
            for subgroup in list(group.subgroups or []):
                found.extend(_collect_entries(subgroup))
            return found

        entries = _collect_entries(recycle)
        subgroups = list(recycle.subgroups or [])
        for entry in entries:
            kp.delete_entry(entry)
        for subgroup in subgroups:
            kp.delete_group(subgroup)
        if entries or subgroups:
            self._dirty = True
            self._invalidate_indexes()
        return len(entries)

    def recycle_bin_uuid(self) -> str | None:
        return self._recycle_bin_uuid()

    def root_group_uuid(self) -> str:
        kp = self._require_kp()
        return str(kp.root_group.uuid)

    def _recycle_bin_uuid(self) -> str | None:
        kp = self._require_kp()
        recycle = kp.recyclebin_group
        return str(recycle.uuid) if recycle is not None else None

    def _require_kp(self) -> PyKeePass:
        if self._kp is None:
            raise DatabaseNotOpenError("Database is not open")
        return self._kp

    def _invalidate_indexes(self) -> None:
        self._entry_by_uuid = None
        self._group_by_uuid = None

    def _ensure_indexes(self) -> None:
        if self._entry_by_uuid is not None and self._group_by_uuid is not None:
            return
        kp = self._require_kp()
        self._entry_by_uuid = {str(entry.uuid): entry for entry in kp.entries}
        self._group_by_uuid = {str(group.uuid): group for group in kp.groups}

    def _find_group(self, group_uuid: str) -> Group:
        self._ensure_indexes()
        assert self._group_by_uuid is not None
        group = self._group_by_uuid.get(group_uuid)
        if group is None:
            raise DatabaseError(f"Group not found: {group_uuid}")
        return group

    def _find_entry(self, entry_uuid: str) -> Any:
        self._ensure_indexes()
        assert self._entry_by_uuid is not None
        entry = self._entry_by_uuid.get(entry_uuid)
        if entry is None:
            raise DatabaseError(f"Entry not found: {entry_uuid}")
        return entry

    def _group_path(self, group: Group, cache: dict[str, str] | None = None) -> str:
        uuid = str(group.uuid)
        if cache is not None and uuid in cache:
            return cache[uuid]
        parts: list[str] = []
        current: Group | None = group
        while current is not None:
            name = current.name or ""
            parts.append(name)
            current = current.parentgroup
        parts.reverse()
        path = "/".join(parts)
        if cache is not None:
            cache[uuid] = path
        return path

    def _is_in_recycle_bin(
        self, entry: Any, *, recycle_uuid: str | None = None
    ) -> bool:
        if recycle_uuid is None:
            recycle_uuid = self._recycle_bin_uuid()
        if recycle_uuid is None or entry.group is None:
            return False
        current = entry.group
        while current is not None:
            if str(current.uuid) == recycle_uuid:
                return True
            current = current.parentgroup
        return False

    def _to_entry_view(
        self,
        entry: Any,
        *,
        recycle_uuid: str | None = None,
        path_cache: dict[str, str] | None = None,
    ) -> EntryView:
        group = entry.group
        props = {
            str(k): str(v) for k, v in dict(entry.custom_properties or {}).items()
        }
        tags_raw = getattr(entry, "tags", None) or []
        tags = tuple(str(t).strip() for t in tags_raw if str(t).strip())
        expiry = ""
        expires = bool(getattr(entry, "expires", False))
        expiry_time = getattr(entry, "expiry_time", None)
        if expiry_time is not None:
            try:
                expiry = expiry_time.isoformat()
            except Exception:
                expiry = str(expiry_time)
        attachments = entry.attachments or []
        return EntryView(
            uuid=str(entry.uuid),
            title=entry.title or "",
            username=entry.username or "",
            password=entry.password or "",
            url=entry.url or "",
            notes=entry.notes or "",
            group_path=(
                self._group_path(group, path_cache) if group is not None else ""
            ),
            custom_properties=props,
            in_recycle_bin=self._is_in_recycle_bin(
                entry, recycle_uuid=recycle_uuid
            ),
            otp=entry.otp or "",
            expires=expires,
            expiry_time=expiry,
            tags=tags,
            attachment_count=len(attachments),
        )
