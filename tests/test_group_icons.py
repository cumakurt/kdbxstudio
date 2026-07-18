"""Group category icon heuristics."""

from kdbxstudio.ui.icons.group_icons import (
    GroupKind,
    detect_group_kind,
    group_icon_for_name,
    group_kind_color,
)


def test_detect_group_kind_keywords() -> None:
    assert detect_group_kind("Internet") is GroupKind.INTERNET
    assert detect_group_kind("Web Sites") is GroupKind.INTERNET
    assert detect_group_kind("Windows Servers") is GroupKind.WINDOWS
    assert detect_group_kind("Linux VMs") is GroupKind.LINUX
    assert detect_group_kind("Ubuntu Hosts") is GroupKind.LINUX
    assert detect_group_kind("macOS Devices") is GroupKind.MACOS
    assert detect_group_kind("SSH Keys") is GroupKind.SSH
    assert detect_group_kind("Docker Swarm") is GroupKind.DOCKER
    assert detect_group_kind("Kubernetes Prod") is GroupKind.KUBERNETES
    assert detect_group_kind("Cloud AWS") is GroupKind.CLOUD
    assert detect_group_kind("VPN Gateways") is GroupKind.VPN
    assert detect_group_kind("PostgreSQL") is GroupKind.DATABASE
    assert detect_group_kind("Email Accounts") is GroupKind.EMAIL
    assert detect_group_kind("Bank Cards") is GroupKind.BANK
    assert detect_group_kind("WiFi Home") is GroupKind.WIFI
    assert detect_group_kind("Crypto Wallets") is GroupKind.CRYPTO
    assert detect_group_kind("API Tokens") is GroupKind.API
    assert detect_group_kind("SSL Certificates") is GroupKind.CERTIFICATE
    assert detect_group_kind("Random Stuff") is GroupKind.FOLDER
    assert detect_group_kind("Trash", is_recycle_bin=True) is GroupKind.RECYCLE


def test_group_icon_renders(qtbot) -> None:
    icon = group_icon_for_name("Linux", size=18)
    assert not icon.isNull()
    assert group_kind_color(GroupKind.LINUX).startswith("#")
    assert not group_icon_for_name("Internet", size=20).isNull()
    assert not group_icon_for_name("Windows", size=20).isNull()
