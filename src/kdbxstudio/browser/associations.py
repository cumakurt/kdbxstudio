"""Persist KeePassXC-Browser association keys in KDBX Meta CustomData."""

from __future__ import annotations

from lxml import etree

from kdbxstudio.core.database import KdbxDatabase

BROWSER_KEY_PREFIX = "KPXC_BROWSER_"
CREATED_PREFIX = "KPXC_BROWSER_CREATED_"  # KeePassXC uses "Created" with prefix helper


def _meta_element(db: KdbxDatabase):
    kp = db._require_kp()  # noqa: SLF001
    root = kp.kdbx.body.payload.xml.getroot()
    meta = root.find("Meta")
    if meta is None:
        raise RuntimeError("KDBX Meta element missing")
    return meta, kp


def _custom_data(meta) -> etree._Element:
    cd = meta.find("CustomData")
    if cd is None:
        cd = etree.SubElement(meta, "CustomData")
    return cd


def list_association_keys(db: KdbxDatabase) -> dict[str, str]:
    meta, _kp = _meta_element(db)
    cd = meta.find("CustomData")
    if cd is None:
        return {}
    out: dict[str, str] = {}
    for item in cd.findall("Item"):
        key_el = item.findtext("Key") or ""
        val_el = item.findtext("Value") or ""
        if key_el.startswith(BROWSER_KEY_PREFIX):
            assoc_id = key_el[len(BROWSER_KEY_PREFIX) :]
            out[assoc_id] = val_el
    return out


def get_association_key(db: KdbxDatabase, assoc_id: str) -> str | None:
    return list_association_keys(db).get(assoc_id)


def set_association_key(db: KdbxDatabase, assoc_id: str, public_key: str) -> None:
    meta, kp = _meta_element(db)
    cd = _custom_data(meta)
    full_key = f"{BROWSER_KEY_PREFIX}{assoc_id}"
    for item in list(cd.findall("Item")):
        if (item.findtext("Key") or "") == full_key:
            value = item.find("Value")
            if value is None:
                value = etree.SubElement(item, "Value")
            value.text = public_key
            db._dirty = True  # noqa: SLF001
            return
    item = etree.SubElement(cd, "Item")
    etree.SubElement(item, "Key").text = full_key
    etree.SubElement(item, "Value").text = public_key
    db._dirty = True  # noqa: SLF001


def database_hash_for(db: KdbxDatabase) -> str:
    """Match KeePassXC: SHA-256 hex of root group UUID without dashes."""
    import hashlib

    root_hex = db._require_kp().root_group.uuid.hex  # noqa: SLF001
    return hashlib.sha256(root_hex.encode("utf-8")).hexdigest()
