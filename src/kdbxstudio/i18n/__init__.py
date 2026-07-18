"""Application internationalization (English default)."""

from __future__ import annotations

from collections.abc import Mapping

from kdbxstudio.i18n.catalog_tr import TR_CATALOG

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "tr")

LANGUAGE_LABELS: Mapping[str, str] = {
    "en": "English",
    "tr": "Türkçe",
}

_catalogs: dict[str, Mapping[str, str]] = {
    "en": {},
    "tr": TR_CATALOG,
}

_current_language = "en"


def normalize_language(code: str | None) -> str:
    value = (code or "en").strip().lower()
    if value.startswith("tr"):
        return "tr"
    if value in SUPPORTED_LANGUAGES:
        return value
    return "en"


def get_language() -> str:
    return _current_language


def set_language(code: str) -> str:
    global _current_language
    _current_language = normalize_language(code)
    return _current_language


def language_choices() -> list[tuple[str, str]]:
    """Return (code, native label) pairs for settings UI."""
    return [(code, LANGUAGE_LABELS[code]) for code in SUPPORTED_LANGUAGES]


def tr(message: str) -> str:
    """Translate *message* using the active language catalog.

    English source strings are the catalog keys. Missing translations fall
    back to the original English text.
    """
    if not message or _current_language == "en":
        return message
    catalog = _catalogs.get(_current_language) or {}
    return catalog.get(message, message)


def trf(template: str, **kwargs: object) -> str:
    """Translate a format template then interpolate kwargs."""
    return tr(template).format(**kwargs)
