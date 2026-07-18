"""KeePassXC-Browser protocol and crypto tests."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from uuid import UUID

from kdbxstudio.browser import associations, crypto
from kdbxstudio.browser.host import _read_native, _write_native
from kdbxstudio.browser.protocol import BrowserProtocol, ProtocolContext, _normalize_uuid
from kdbxstudio.core.database import EntryView, KdbxDatabase


def test_crypto_roundtrip_and_nonce_increment() -> None:
    pk_a, sk_a = crypto.generate_keypair()
    pk_b, sk_b = crypto.generate_keypair()
    nonce = crypto.random_nonce_b64()
    plain = '{"action":"get-databasehash","hash":"abc"}'
    encrypted = crypto.encrypt_json(plain, nonce, pk_b, sk_a)
    decrypted = crypto.decrypt_json(encrypted, nonce, pk_a, sk_b)
    assert decrypted == plain
    bumped = crypto.increment_nonce(nonce)
    assert bumped != nonce
    # second increment differs again
    assert crypto.increment_nonce(bumped) != bumped


def test_normalize_uuid_hex() -> None:
    dashed = "12345678-1234-5678-1234-567812345678"
    hexed = dashed.replace("-", "")
    assert _normalize_uuid(hexed) == dashed
    assert _normalize_uuid(dashed) == dashed


def test_database_hash_matches_keepassxc_shape(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "hash.kdbx", password="secret")
    digest = associations.database_hash_for(db)
    assert len(digest) == 64
    root_hex = db._require_kp().root_group.uuid.hex  # noqa: SLF001
    import hashlib

    assert digest == hashlib.sha256(root_hex.encode("utf-8")).hexdigest()
    db.close()


def _make_protocol(tmp_path: Path, *, assoc_id: str = "firefox") -> tuple[
    BrowserProtocol, KdbxDatabase, EntryView
]:
    db = KdbxDatabase()
    path = tmp_path / "browser.kdbx"
    db.create(path, password="secret")
    root = db.root_group_uuid()
    entry = db.add_entry(
        root,
        title="GitHub",
        username="dev",
        password="hunter2",
        url="https://github.com/login",
    )

    def get_database():
        return db

    def get_entries():
        return db.list_entries(include_recycle_bin=False)

    def list_groups():
        return db.list_groups()

    protocol = BrowserProtocol(
        ProtocolContext(
            get_database=get_database,
            get_entries=get_entries,
            list_groups=list_groups,
            prompt_associate=lambda _label: assoc_id,
            lock_database=lambda: None,
            ensure_group_path=db.ensure_group_path,
            add_entry=lambda group_uuid, title, username="", password="", url="", **_k: db.add_entry(
                group_uuid,
                title=title,
                username=username,
                password=password,
                url=url,
            ),
            update_entry=lambda uuid, **kwargs: db.update_entry(uuid, **kwargs),
            get_entry=db.get_entry,
        )
    )
    return protocol, db, entry


def test_protocol_associate_and_get_logins(tmp_path: Path) -> None:
    protocol, db, entry = _make_protocol(tmp_path)
    client_pk, client_sk = crypto.generate_keypair()
    client_id = "client-1"
    nonce = crypto.random_nonce_b64()

    cpk = protocol.handle(
        {
            "action": "change-public-keys",
            "publicKey": client_pk,
            "nonce": nonce,
            "clientID": client_id,
        }
    )
    assert cpk.get("success") == crypto.TRUE_STR
    assert "publicKey" in cpk
    assert "nonce" in cpk
    host_pk = cpk["publicKey"]
    session = protocol.sessions[client_id]

    # associate
    assoc_nonce = crypto.random_nonce_b64()
    assoc_plain = json.dumps(
        {
            "action": "associate",
            "key": client_pk,
            "idKey": client_pk,
        },
        separators=(",", ":"),
    )
    assoc_msg = crypto.encrypt_json(
        assoc_plain, assoc_nonce, session.host_public_key, client_sk
    )
    assoc_resp = protocol.handle(
        {
            "action": "associate",
            "message": assoc_msg,
            "nonce": assoc_nonce,
            "clientID": client_id,
        }
    )
    assert "message" in assoc_resp
    assoc_body = json.loads(
        crypto.decrypt_json(
            assoc_resp["message"],
            assoc_resp["nonce"],
            session.host_public_key,
            client_sk,
        )
    )
    assert assoc_body["success"] == crypto.TRUE_STR
    assert assoc_body["id"] == "firefox"
    assert associations.get_association_key(db, "firefox") == client_pk

    # test-associate
    test_nonce = crypto.random_nonce_b64()
    test_plain = json.dumps(
        {"action": "test-associate", "id": "firefox", "key": client_pk},
        separators=(",", ":"),
    )
    test_msg = crypto.encrypt_json(
        test_plain, test_nonce, session.host_public_key, client_sk
    )
    test_resp = protocol.handle(
        {
            "action": "test-associate",
            "message": test_msg,
            "nonce": test_nonce,
            "clientID": client_id,
        }
    )
    assert "message" in test_resp

    # get-logins
    login_nonce = crypto.random_nonce_b64()
    login_plain = json.dumps(
        {
            "action": "get-logins",
            "url": "https://github.com/settings",
            "id": "firefox",
            "keys": [{"id": "firefox", "key": client_pk}],
        },
        separators=(",", ":"),
    )
    login_msg = crypto.encrypt_json(
        login_plain, login_nonce, session.host_public_key, client_sk
    )
    login_resp = protocol.handle(
        {
            "action": "get-logins",
            "message": login_msg,
            "nonce": login_nonce,
            "clientID": client_id,
        }
    )
    body = json.loads(
        crypto.decrypt_json(
            login_resp["message"],
            login_resp["nonce"],
            session.host_public_key,
            client_sk,
        )
    )
    assert body["count"] == "1"
    assert body["entries"][0]["login"] == "dev"
    assert body["entries"][0]["password"] == "hunter2"
    assert body["entries"][0]["uuid"] == UUID(entry.uuid).hex

    # get-databasehash
    hash_nonce = crypto.random_nonce_b64()
    hash_plain = json.dumps({"action": "get-databasehash"}, separators=(",", ":"))
    hash_msg = crypto.encrypt_json(
        hash_plain, hash_nonce, session.host_public_key, client_sk
    )
    hash_resp = protocol.handle(
        {
            "action": "get-databasehash",
            "message": hash_msg,
            "nonce": hash_nonce,
            "clientID": client_id,
        }
    )
    hash_body = json.loads(
        crypto.decrypt_json(
            hash_resp["message"],
            hash_resp["nonce"],
            session.host_public_key,
            client_sk,
        )
    )
    assert hash_body["hash"] == associations.database_hash_for(db)
    db.close()


def test_native_messaging_framing(monkeypatch) -> None:
    payload = {"action": "change-public-keys", "success": "true"}
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    framed = struct.pack("<I", len(encoded)) + encoded

    class _Buf:
        def __init__(self, data: bytes) -> None:
            self._data = data
            self._pos = 0
            self.written = b""

        def read(self, n: int) -> bytes:
            chunk = self._data[self._pos : self._pos + n]
            self._pos += len(chunk)
            return chunk

        def write(self, data: bytes) -> int:
            self.written += data
            return len(data)

        def flush(self) -> None:
            pass

    class _Stdio:
        def __init__(self, buf: _Buf) -> None:
            self.buffer = buf

    import sys

    stdin_buf = _Buf(framed)
    stdout_buf = _Buf(b"")
    monkeypatch.setattr(sys, "stdin", _Stdio(stdin_buf))
    monkeypatch.setattr(sys, "stdout", _Stdio(stdout_buf))

    message = _read_native()
    assert message == payload
    _write_native(payload)
    assert stdout_buf.written[:4] == struct.pack("<I", len(encoded))
    assert stdout_buf.written[4:] == encoded
