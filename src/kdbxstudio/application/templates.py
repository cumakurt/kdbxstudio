"""Secret entry templates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    secret: bool = False
    default: str = ""


@dataclass(frozen=True)
class EntryTemplate:
    id: str
    name: str
    description: str
    title_prefix: str = ""
    fields: tuple[FieldSpec, ...] = ()
    notes_placeholder: str = ""
    custom_defaults: dict[str, str] = field(default_factory=dict)


TEMPLATES: tuple[EntryTemplate, ...] = (
    EntryTemplate(
        id="login",
        name="Login",
        description="Username / password / URL",
        fields=(
            FieldSpec("username", "Username"),
            FieldSpec("password", "Password", secret=True),
            FieldSpec("url", "URL"),
        ),
    ),
    EntryTemplate(
        id="api_key",
        name="API Key",
        description="Service API credential",
        fields=(FieldSpec("password", "API Key", secret=True),),
        custom_defaults={"Type": "API Key"},
        notes_placeholder="Service:\nScopes:\n",
    ),
    EntryTemplate(
        id="ssh_key",
        name="SSH Key",
        description="SSH private key material",
        fields=(FieldSpec("username", "Comment / user"),),
        custom_defaults={"Type": "SSH Key"},
        notes_placeholder=(
            "-----BEGIN OPENSSH PRIVATE KEY-----\n\n"
            "-----END OPENSSH PRIVATE KEY-----\n"
        ),
    ),
    EntryTemplate(
        id="certificate",
        name="Certificate",
        description="X.509 / PEM certificate",
        custom_defaults={"Type": "Certificate"},
        notes_placeholder=(
            "-----BEGIN CERTIFICATE-----\n\n-----END CERTIFICATE-----\n"
        ),
    ),
    EntryTemplate(
        id="secure_note",
        name="Secure Note",
        description="Free-form protected note",
        notes_placeholder="",
    ),
    EntryTemplate(
        id="bank_card",
        name="Bank Card",
        description="Payment card details",
        fields=(
            FieldSpec("username", "Cardholder"),
            FieldSpec("password", "Number", secret=True),
        ),
        custom_defaults={"Type": "Bank Card", "Expiry": "", "CVV": ""},
    ),
)


def get_template(template_id: str) -> EntryTemplate | None:
    for template in TEMPLATES:
        if template.id == template_id:
            return template
    return None


def list_templates() -> list[EntryTemplate]:
    return list(TEMPLATES)
