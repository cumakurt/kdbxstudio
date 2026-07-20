"""KeePassXC-Browser protocol action handlers."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from kdbxstudio.application.browser_bridge import match_logins_for_url
from kdbxstudio.browser import associations, crypto
from kdbxstudio.core.database import EntryView, KdbxDatabase
from kdbxstudio.core.password_generator import GeneratorOptions, generate_password
from kdbxstudio.core.totp import current_totp

# Error codes from KeePassXC BrowserMessageBuilder.h
ERR_DB_NOT_OPENED = 1
ERR_DB_HASH = 2
ERR_CLIENT_PK = 3
ERR_DECRYPT = 4
ERR_DENIED = 6
ERR_ENCRYPT = 7
ERR_ASSOCIATION = 8
ERR_KEY_UNRECOGNIZED = 10
ERR_INCORRECT_ACTION = 12
ERR_EMPTY = 13
ERR_NO_URL = 14
ERR_NO_LOGINS = 15
ERR_NO_GROUPS = 16
ERR_NO_UUID = 18
MAX_CLIENT_SESSIONS = 64


AssociatePrompt = Callable[[str], str | None]  # db_label -> association id or None
LockCallback = Callable[[], None]


@dataclass
class ClientSession:
    client_public_key: str = ""
    host_public_key: str = ""
    host_secret_key: str = ""
    associated: bool = False


@dataclass
class ProtocolContext:
    """Runtime hooks provided by the UI / database manager."""

    get_database: Callable[[], KdbxDatabase | None]
    get_entries: Callable[[], list[EntryView]]
    list_groups: Callable[[], list[Any]]
    prompt_associate: AssociatePrompt
    lock_database: LockCallback
    ensure_group_path: Callable[[str], str] | None = None
    add_entry: Callable[..., EntryView] | None = None
    update_entry: Callable[..., EntryView] | None = None
    get_entry: Callable[[str], EntryView | None] | None = None
    is_read_only: Callable[[], bool] = lambda: False
    version: str = crypto.VERSION


EncryptedHandler = Callable[
    [dict[str, Any], ClientSession, KdbxDatabase, str],
    dict[str, Any] | None,
]


@dataclass
class BrowserProtocol:
    """Stateful KeePassXC-Browser protocol (one session per clientID)."""

    context: ProtocolContext
    sessions: dict[str, ClientSession] = field(default_factory=dict)

    def handle(self, request: dict) -> dict:
        if not request:
            return self._error("", ERR_EMPTY)
        action = str(request.get("action") or "")
        if not action:
            return self._error(action, ERR_INCORRECT_ACTION)

        if action == "change-public-keys":
            return self._change_public_keys(request)

        client_id = str(request.get("clientID") or "")
        session = self.sessions.get(client_id)
        db = self.context.get_database()
        if action != "request-autotype" and db is None:
            if session is None or not session.client_public_key:
                return self._error(action, ERR_CLIENT_PK)
            return self._error(action, ERR_DB_NOT_OPENED)

        if action == "get-databasehash":
            return self._encrypted_action(request, session, self._get_databasehash)
        if action == "associate":
            return self._encrypted_action(request, session, self._associate)
        if action == "test-associate":
            return self._encrypted_action(request, session, self._test_associate)
        if action == "get-logins":
            return self._encrypted_action(request, session, self._get_logins)
        if action == "get-logins-count":
            return self._encrypted_action(request, session, self._get_logins_count)
        if action == "set-login":
            return self._encrypted_action(request, session, self._set_login)
        if action == "generate-password":
            return self._generate_password(request, session)
        if action == "get-database-groups":
            return self._encrypted_action(request, session, self._get_database_groups)
        if action == "create-new-group":
            return self._encrypted_action(request, session, self._create_new_group)
        if action == "get-totp":
            return self._encrypted_action(request, session, self._get_totp)
        if action == "lock-database":
            return self._encrypted_action(request, session, self._lock_database)
        if action == "request-autotype":
            # Best-effort ack; Auto-Type is handled in the desktop UI.
            return self._error(action, ERR_INCORRECT_ACTION)
        return self._error(action, ERR_INCORRECT_ACTION)

    def _change_public_keys(self, request: dict) -> dict:
        nonce = str(request.get("nonce") or "")
        client_pk = str(request.get("publicKey") or "")
        client_id = str(request.get("clientID") or "")
        if not nonce or not client_pk or not client_id:
            return self._error("change-public-keys", ERR_CLIENT_PK)
        try:
            client_key_bytes = crypto.b64decode(client_pk)
            incremented = crypto.increment_nonce(nonce)
        except ValueError:
            return self._error("change-public-keys", ERR_CLIENT_PK)
        if len(client_key_bytes) != 32:
            return self._error("change-public-keys", ERR_CLIENT_PK)
        host_pk, host_sk = crypto.generate_keypair()
        if client_id not in self.sessions and len(self.sessions) >= MAX_CLIENT_SESSIONS:
            self.sessions.pop(next(iter(self.sessions)))
        self.sessions[client_id] = ClientSession(
            client_public_key=client_pk,
            host_public_key=host_pk,
            host_secret_key=host_sk,
            associated=False,
        )
        return {
            "action": "change-public-keys",
            "version": self.context.version,
            "publicKey": host_pk,
            "nonce": incremented,
            "success": crypto.TRUE_STR,
        }

    def _encrypted_action(
        self,
        request: dict,
        session: ClientSession | None,
        handler: EncryptedHandler,
    ) -> dict:
        action = str(request.get("action") or "")
        if session is None or not session.host_secret_key:
            return self._error(action, ERR_CLIENT_PK)
        nonce = str(request.get("nonce") or "")
        encrypted = str(request.get("message") or "")
        if not nonce or not encrypted:
            return self._error(action, ERR_DECRYPT)
        try:
            plain = crypto.decrypt_json(
                encrypted,
                nonce,
                session.client_public_key,
                session.host_secret_key,
            )
            payload = json.loads(plain)
        except Exception:
            return self._error(action, ERR_DECRYPT)
        if not isinstance(payload, dict):
            return self._error(action, ERR_DECRYPT)
        db = self.context.get_database()
        if db is None:
            return self._error(action, ERR_DB_NOT_OPENED)
        db_hash = associations.database_hash_for(db)
        incremented = crypto.increment_nonce(nonce)
        try:
            params = handler(payload, session, db, db_hash)
        except _ProtocolError as exc:
            return self._error(action, exc.code)
        if params is None:
            return self._error(action, ERR_DENIED)
        return self._build_response(action, incremented, params, session)

    def _get_databasehash(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        return {"hash": db_hash, "action": "hash"}

    def _associate(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        if self.context.is_read_only():
            raise _ProtocolError(ERR_DENIED)
        key = str(payload.get("key") or "")
        if not key or key != session.client_public_key:
            raise _ProtocolError(ERR_ASSOCIATION)
        id_key = str(payload.get("idKey") or key)
        label = db.path.name if db.path else "Database"
        assoc_id = self.context.prompt_associate(label)
        if not assoc_id:
            raise _ProtocolError(ERR_DENIED)
        assoc_id = assoc_id.strip()
        if not assoc_id or len(assoc_id) > 128:
            raise _ProtocolError(ERR_DENIED)
        associations.set_association_key(db, assoc_id, id_key)
        session.associated = True
        return {"hash": db_hash, "id": assoc_id}

    def _test_associate(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        assoc_id = str(payload.get("id") or "")
        key = str(payload.get("key") or "")
        if not assoc_id or not key:
            raise _ProtocolError(ERR_DB_NOT_OPENED)
        stored = associations.get_association_key(db, assoc_id)
        if not stored or stored != key:
            raise _ProtocolError(ERR_ASSOCIATION)
        session.associated = True
        return {"hash": db_hash, "id": assoc_id}

    def _require_associated(self, session: ClientSession) -> None:
        if not session.associated:
            raise _ProtocolError(ERR_ASSOCIATION)

    def _get_logins(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        url = str(payload.get("url") or "")
        if not url:
            raise _ProtocolError(ERR_NO_URL)
        if not self._keys_ok(payload, db):
            raise _ProtocolError(ERR_ASSOCIATION)
        hits = match_logins_for_url(self.context.get_entries(), url)
        if not hits:
            raise _ProtocolError(ERR_NO_LOGINS)
        entries = [
            {
                "login": e.username,
                "name": e.title,
                "password": e.password,
                "uuid": _uuid_hex(e.uuid),
                "group": e.group_path,
            }
            for e in hits
        ]
        return {
            "count": str(len(entries)),
            "entries": entries,
            "hash": db_hash,
            "id": str(payload.get("id") or ""),
        }

    def _get_logins_count(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        url = str(payload.get("url") or "")
        if not self._keys_ok(payload, db):
            raise _ProtocolError(ERR_ASSOCIATION)
        hits = match_logins_for_url(self.context.get_entries(), url) if url else []
        return {"count": str(len(hits)), "hash": db_hash}

    def _set_login(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        if self.context.is_read_only():
            raise _ProtocolError(ERR_DENIED)
        if self.context.add_entry is None or self.context.update_entry is None:
            raise _ProtocolError(ERR_DENIED)
        url = str(payload.get("url") or "")
        if not url:
            raise _ProtocolError(ERR_NO_URL)
        login = str(payload.get("login") or "")
        password = str(payload.get("password") or "")
        uuid = str(payload.get("uuid") or "")
        group_uuid = str(payload.get("groupUuid") or "")
        group_name = str(payload.get("group") or "")
        submit_url = str(payload.get("submitUrl") or "")
        title = url_host_title(url) or login or "Browser login"
        entry_uuid = _normalize_uuid(uuid) if uuid else ""
        group_id = _normalize_uuid(group_uuid) if group_uuid else ""
        existing = None
        if entry_uuid and self.context.get_entry:
            existing = self.context.get_entry(entry_uuid) or self.context.get_entry(
                uuid
            )
        if existing is not None:
            self.context.update_entry(
                existing.uuid,
                title=title,
                username=login,
                password=password,
                url=url,
            )
        else:
            target_group = group_id
            if not target_group and self.context.ensure_group_path:
                path = group_name or "Root/KeePassXC-Browser Passwords"
                target_group = self.context.ensure_group_path(path)
            if not target_group:
                target_group = db.root_group_uuid()
            self.context.add_entry(
                target_group,
                title=title,
                username=login,
                password=password,
                url=url or submit_url,
            )
        return {"count": None, "entries": None, "error": "", "hash": db_hash}

    def _generate_password(self, request: dict, session: ClientSession | None) -> dict:
        action = "generate-password"
        if session is None:
            return self._error(action, ERR_CLIENT_PK)
        if not session.associated:
            return self._error(action, ERR_ASSOCIATION)
        nonce = str(request.get("nonce") or "")
        if not nonce:
            return self._error(action, ERR_DECRYPT)
        # Message may be empty for generate-password
        incremented = crypto.increment_nonce(nonce)
        password = generate_password(GeneratorOptions(length=20))
        request_id = str(request.get("requestID") or "")
        params: dict[str, Any] = {"password": password}
        if request_id:
            # Also echo requestID on the outer response for older clients
            response = self._build_response(action, incremented, params, session)
            response["requestID"] = request_id
            return response
        return self._build_response(action, incremented, params, session)

    def _get_database_groups(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        groups = self.context.list_groups()
        if not groups:
            raise _ProtocolError(ERR_NO_GROUPS)
        by_parent: dict[str | None, list[Any]] = {}
        for g in groups:
            by_parent.setdefault(g.parent_uuid, []).append(g)

        def build(node: Any) -> dict[str, Any]:
            children = [build(c) for c in by_parent.get(node.uuid, [])]
            return {
                "name": node.name or "Root",
                "uuid": _uuid_hex(node.uuid),
                "children": children,
            }

        roots = by_parent.get(None) or []
        if not roots:
            # Fall back: groups whose parent is missing
            root_uuid = db.root_group_uuid()
            roots = [g for g in groups if g.uuid == root_uuid]
        tree = [build(r) for r in roots]
        return {
            "defaultGroup": "Root",
            "defaultGroupAlwaysAllow": False,
            "groups": tree,
        }

    def _create_new_group(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        if self.context.is_read_only():
            raise _ProtocolError(ERR_DENIED)
        name = str(payload.get("groupName") or "").strip()
        if not name or self.context.ensure_group_path is None:
            raise _ProtocolError(ERR_DENIED)
        uuid = self.context.ensure_group_path(name)
        leaf = name.replace("\\", "/").rstrip("/").split("/")[-1]
        return {"name": leaf, "uuid": _uuid_hex(uuid)}

    def _get_totp(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        raw_uuid = str(payload.get("uuid") or "")
        if not raw_uuid or self.context.get_entry is None:
            raise _ProtocolError(ERR_NO_UUID)
        entry = self.context.get_entry(
            _normalize_uuid(raw_uuid)
        ) or self.context.get_entry(raw_uuid)
        if entry is None or not entry.otp:
            raise _ProtocolError(ERR_NO_UUID)
        status = current_totp(entry.otp)
        return {"totp": status.code or ""}

    def _lock_database(
        self, payload: dict, session: ClientSession, db: KdbxDatabase, db_hash: str
    ) -> dict:
        self._require_associated(session)
        self.context.lock_database()
        # KeePassXC returns an error-shaped payload even on success historically;
        # modern clients accept success.
        return {"hash": db_hash}

    def _keys_ok(self, payload: dict, db: KdbxDatabase) -> bool:
        """Verify association key material. Fail closed when nothing is provided."""
        keys = payload.get("keys") or []
        if not isinstance(keys, list) or not keys:
            # Some clients only send id/key at top level after associate
            assoc_id = str(payload.get("id") or "")
            key = str(payload.get("key") or "")
            if assoc_id and key:
                stored = associations.get_association_key(db, assoc_id)
                return bool(stored and stored == key)
            return False
        for item in keys:
            if not isinstance(item, dict):
                continue
            assoc_id = str(item.get("id") or "")
            key = str(item.get("key") or "")
            stored = associations.get_association_key(db, assoc_id)
            if stored and stored == key:
                return True
        return False

    def _build_response(
        self, action: str, nonce: str, params: dict, session: ClientSession
    ) -> dict:
        message = {
            "version": self.context.version,
            "success": crypto.TRUE_STR,
            "nonce": nonce,
        }
        message.update(params)
        try:
            encrypted = crypto.encrypt_json(
                json.dumps(message, separators=(",", ":")),
                nonce,
                session.client_public_key,
                session.host_secret_key,
            )
        except Exception:
            return self._error(action, ERR_ENCRYPT)
        return {"action": action, "message": encrypted, "nonce": nonce}

    @staticmethod
    def _error(action: str, code: int) -> dict:
        messages = {
            ERR_DB_NOT_OPENED: "Database not opened",
            ERR_DB_HASH: "Database hash not available",
            ERR_CLIENT_PK: "Client public key not received",
            ERR_DECRYPT: "Cannot decrypt message",
            ERR_DENIED: "Action cancelled or denied",
            ERR_ENCRYPT: "Message encryption failed.",
            ERR_ASSOCIATION: "KeePassXC association failed, try again",
            ERR_KEY_UNRECOGNIZED: "Encryption key is not recognized",
            ERR_INCORRECT_ACTION: "Incorrect action",
            ERR_EMPTY: "Empty message received",
            ERR_NO_URL: "No URL provided",
            ERR_NO_LOGINS: "No logins found",
            ERR_NO_GROUPS: "No groups found",
            ERR_NO_UUID: "No valid UUID provided",
        }
        return {
            "action": action,
            "errorCode": str(code),
            "error": messages.get(code, "Error"),
        }


class _ProtocolError(Exception):
    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(str(code))


def _uuid_hex(value: str) -> str:
    try:
        return UUID(value).hex
    except ValueError:
        return value.replace("-", "").lower()


def _normalize_uuid(value: str) -> str:
    raw = value.replace("-", "").lower()
    if len(raw) == 32:
        return str(UUID(hex=raw))
    return value


def url_host_title(url: str) -> str:
    from kdbxstudio.application.browser_bridge import url_host

    return url_host(url)
