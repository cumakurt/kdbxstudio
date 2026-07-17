"""Database session manager for one or more open KDBX files."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from kdbxstudio.application.import_csv import ImportResult, import_entries_csv
from kdbxstudio.core.cache import Cache
from kdbxstudio.core.database import (
    AttachmentView,
    DatabaseInfo,
    EntryView,
    GroupView,
    HistoryView,
    KdbxDatabase,
)


class DatabaseManager:
    """Owns open database sessions and notifies listeners on changes."""

    def __init__(self) -> None:
        self._databases: dict[str, KdbxDatabase] = {}
        self._active_id: str | None = None
        self._index_cache: Cache[str, list[EntryView]] = Cache()
        self._listeners: list[Callable[[], None]] = []

    @property
    def active(self) -> KdbxDatabase | None:
        if self._active_id is None:
            return None
        return self._databases.get(self._active_id)

    @property
    def active_id(self) -> str | None:
        return self._active_id

    def session_ids(self) -> list[str]:
        return list(self._databases.keys())

    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def open(
        self,
        path: Path | str,
        password: str | None = None,
        keyfile: Path | str | None = None,
        *,
        make_active: bool = True,
    ) -> str:
        path = Path(path).resolve()
        session_id = str(path)
        db = KdbxDatabase()
        db.open(path, password=password, keyfile=keyfile)
        if session_id in self._databases:
            self._databases[session_id].close()
        self._databases[session_id] = db
        self._invalidate(session_id)
        if make_active or self._active_id is None:
            self._active_id = session_id
        self._notify()
        return session_id

    def create(
        self,
        path: Path | str,
        password: str | None = None,
        keyfile: Path | str | None = None,
        *,
        make_active: bool = True,
    ) -> str:
        path = Path(path).resolve()
        session_id = str(path)
        db = KdbxDatabase()
        db.create(path, password=password, keyfile=keyfile)
        if session_id in self._databases:
            self._databases[session_id].close()
        self._databases[session_id] = db
        self._invalidate(session_id)
        if make_active or self._active_id is None:
            self._active_id = session_id
        self._notify()
        return session_id

    def set_active(self, session_id: str) -> None:
        if session_id not in self._databases:
            raise KeyError(f"Unknown session: {session_id}")
        self._active_id = session_id
        self._notify()

    def close(self, session_id: str | None = None) -> None:
        target = session_id or self._active_id
        if target is None:
            return
        db = self._databases.pop(target, None)
        if db is not None:
            db.close()
        self._invalidate(target)
        if self._active_id == target:
            self._active_id = next(iter(self._databases), None)
        self._notify()

    def close_all(self) -> None:
        for db in self._databases.values():
            db.close()
        self._databases.clear()
        self._index_cache.clear()
        self._active_id = None
        self._notify()

    def save(self, session_id: str | None = None) -> None:
        db = self._get(session_id)
        db.save()
        self._notify()

    def list_groups(self, session_id: str | None = None) -> list[GroupView]:
        return self._get(session_id).list_groups()

    def add_group(
        self,
        parent_uuid: str,
        name: str,
        session_id: str | None = None,
    ) -> GroupView:
        group = self._get(session_id).add_group(parent_uuid, name)
        self._invalidate(session_id or self._active_id)
        self._notify()
        return group

    def rename_group(
        self,
        group_uuid: str,
        name: str,
        session_id: str | None = None,
    ) -> GroupView:
        group = self._get(session_id).rename_group(group_uuid, name)
        self._invalidate(session_id or self._active_id)
        self._notify()
        return group

    def delete_group(
        self,
        group_uuid: str,
        session_id: str | None = None,
        *,
        permanent: bool = False,
    ) -> None:
        self._get(session_id).delete_group(group_uuid, permanent=permanent)
        self._invalidate(session_id or self._active_id)
        self._notify()

    def ensure_group_path(
        self, path: str, session_id: str | None = None
    ) -> str:
        uuid = self._get(session_id).ensure_group_path(path)
        self._invalidate(session_id or self._active_id)
        self._notify()
        return uuid

    def change_credentials(
        self,
        *,
        password: str | None = None,
        keyfile: Path | str | None = None,
        clear_keyfile: bool = False,
        session_id: str | None = None,
    ) -> None:
        self._get(session_id).change_credentials(
            password=password,
            keyfile=keyfile,
            clear_keyfile=clear_keyfile,
        )
        self._notify()

    def import_csv(
        self,
        path: Path | str,
        session_id: str | None = None,
    ) -> ImportResult:
        result = import_entries_csv(self._get(session_id), path)
        self._invalidate(session_id or self._active_id)
        self._notify()
        return result

    def list_entries(
        self,
        group_uuid: str | None = None,
        session_id: str | None = None,
    ) -> list[EntryView]:
        return self._get(session_id).list_entries(group_uuid)

    def get_entry(
        self, entry_uuid: str, session_id: str | None = None
    ) -> EntryView | None:
        return self._get(session_id).get_entry(entry_uuid)

    def add_entry(
        self,
        group_uuid: str,
        title: str,
        username: str = "",
        password: str = "",
        url: str = "",
        notes: str = "",
        session_id: str | None = None,
    ) -> EntryView:
        entry = self._get(session_id).add_entry(
            group_uuid,
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
        )
        self._invalidate(session_id or self._active_id)
        self._notify()
        return entry

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
        session_id: str | None = None,
    ) -> EntryView:
        entry = self._get(session_id).update_entry(
            entry_uuid,
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            otp=otp,
            custom_properties=custom_properties,
        )
        self._invalidate(session_id or self._active_id)
        self._notify()
        return entry

    def list_history(
        self, entry_uuid: str, session_id: str | None = None
    ) -> list[HistoryView]:
        return self._get(session_id).list_history(entry_uuid)

    def restore_history(
        self,
        entry_uuid: str,
        history_index: int,
        session_id: str | None = None,
    ) -> EntryView:
        entry = self._get(session_id).restore_history(entry_uuid, history_index)
        self._invalidate(session_id or self._active_id)
        self._notify()
        return entry

    def database_info(self, session_id: str | None = None) -> DatabaseInfo:
        return self._get(session_id).database_info()

    def list_attachments(
        self, entry_uuid: str, session_id: str | None = None
    ) -> list[AttachmentView]:
        return self._get(session_id).list_attachments(entry_uuid)

    def add_attachment(
        self,
        entry_uuid: str,
        filename: str,
        data: bytes,
        session_id: str | None = None,
    ) -> AttachmentView:
        attachment = self._get(session_id).add_attachment(
            entry_uuid, filename, data
        )
        self._notify()
        return attachment

    def delete_attachment(
        self,
        entry_uuid: str,
        attachment_id: int,
        session_id: str | None = None,
    ) -> None:
        self._get(session_id).delete_attachment(entry_uuid, attachment_id)
        self._notify()

    def delete_entry(
        self,
        entry_uuid: str,
        session_id: str | None = None,
        *,
        permanent: bool = False,
    ) -> None:
        self._get(session_id).delete_entry(entry_uuid, permanent=permanent)
        self._invalidate(session_id or self._active_id)
        self._notify()

    def empty_recycle_bin(self, session_id: str | None = None) -> int:
        count = self._get(session_id).empty_recycle_bin()
        self._invalidate(session_id or self._active_id)
        self._notify()
        return count

    def recycle_bin_uuid(self, session_id: str | None = None) -> str | None:
        return self._get(session_id).recycle_bin_uuid()

    def root_group_uuid(self, session_id: str | None = None) -> str:
        return self._get(session_id).root_group_uuid()

    def all_entries(
        self,
        session_id: str | None = None,
        *,
        include_recycle_bin: bool = True,
    ) -> list[EntryView]:
        sid = session_id or self._active_id
        if sid is None:
            return []
        cached = self._index_cache.get(sid)
        if cached is None:
            cached = self._get(sid).list_entries()
            self._index_cache.set(sid, cached)
        if include_recycle_bin:
            return cached
        return [e for e in cached if not e.in_recycle_bin]

    def display_name(self, session_id: str | None = None) -> str:
        db = self._get(session_id)
        if db.path is None:
            return "Untitled"
        dirty = " *" if db.is_dirty else ""
        return f"{db.path.name}{dirty}"

    def any_dirty(self) -> bool:
        return any(db.is_dirty for db in self._databases.values())

    def session_paths(self) -> list[Path]:
        paths: list[Path] = []
        for db in self._databases.values():
            if db.path is not None:
                paths.append(db.path)
        return paths

    def _invalidate(self, session_id: str | None) -> None:
        if session_id:
            self._index_cache.delete(session_id)

    def _get(self, session_id: str | None) -> KdbxDatabase:
        sid = session_id or self._active_id
        if sid is None:
            raise RuntimeError("No active database session")
        db = self._databases.get(sid)
        if db is None:
            raise KeyError(f"Unknown session: {sid}")
        return db

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
