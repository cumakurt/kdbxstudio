"""Core Security Dashboard panels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from kdbxstudio.application.security_dashboard.models import DashboardSnapshot
from kdbxstudio.i18n import tr, trf
from kdbxstudio.ui.charts import (
    BarChartWidget,
    DonutChartWidget,
    GaugeWidget,
    HeatMapWidget,
    KpiCard,
    TimelineList,
)
from kdbxstudio.ui.security_dashboard.panel_base import DashboardPanel
from kdbxstudio.ui.security_dashboard.panel_registry import register_panel


class ScoreHeaderPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Security Score", parent)
        self._gauge = GaugeWidget()
        self._gauge.setMinimumHeight(180)
        row = QHBoxLayout()
        row.addWidget(self._gauge, stretch=1)
        self._kpis = [
            KpiCard(tr("Entries")),
            KpiCard(tr("Findings")),
            KpiCard(tr("Critical")),
            KpiCard(tr("OTP coverage")),
        ]
        col = QHBoxLayout()
        for card in self._kpis:
            col.addWidget(card)
        wrap = QWidget()
        wrap.setLayout(col)
        row.addWidget(wrap, stretch=2)
        self._body.addLayout(row)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        tone = (
            "success"
            if snapshot.security_score >= 75
            else "warning"
            if snapshot.security_score >= 50
            else "danger"
        )
        self._gauge.set_data(
            snapshot.security_score,
            label=tr(snapshot.score_label),
            caption=tr("Security Score"),
        )
        self._kpis[0].set_value(str(snapshot.total_entries))
        self._kpis[1].set_value(str(len(snapshot.findings)))
        self._kpis[2].set_value(str(snapshot.risk_critical), tone="danger")
        coverage = 0
        if snapshot.total_entries:
            coverage = int(100 * snapshot.otp_with / snapshot.total_entries)
        self._kpis[3].set_value(f"{coverage}%", tone=tone)


class PasswordStatsPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Password Statistics", parent)
        self._donut = DonutChartWidget()
        self._donut.setMinimumHeight(180)
        self._body.addWidget(self._donut)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._donut.set_slices(
            [
                (tr("Strong"), snapshot.strength_strong),
                (tr("Good"), snapshot.strength_good),
                (tr("Fair"), snapshot.strength_fair),
                (tr("Weak"), snapshot.strength_weak),
                (tr("Very Weak"), snapshot.strength_very_weak),
                (tr("Empty"), snapshot.strength_empty),
            ],
            center=str(snapshot.total_passwords),
        )


class DuplicatesPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Duplicate Password Report", parent)
        self._cards = [
            KpiCard(tr("Reused passwords")),
            KpiCard(tr("Most reused")),
            KpiCard(tr("Total reuses")),
        ]
        row = QHBoxLayout()
        for card in self._cards:
            row.addWidget(card)
        self._body.addLayout(row)
        self._list = QLabel("")
        self._list.setWordWrap(True)
        self._list.setObjectName("securityPanelHint")
        self._body.addWidget(self._list)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        risk = "success"
        if snapshot.duplicate_total_reuses >= 10:
            risk = "danger"
        elif snapshot.duplicate_total_reuses > 0:
            risk = "warning"
        self._cards[0].set_value(str(snapshot.duplicate_password_groups), tone=risk)
        self._cards[1].set_value(str(snapshot.most_reused_password_count), tone=risk)
        self._cards[2].set_value(str(snapshot.duplicate_total_reuses), tone=risk)
        if snapshot.duplicate_groups:
            lines = [
                trf(
                    "{n} entries: {titles}",
                    n=g.entry_count,
                    titles=", ".join(g.titles[:4]),
                )
                for g in snapshot.duplicate_groups[:5]
            ]
            self._list.setText("\n".join(lines))
        else:
            self._list.setText(tr("No duplicate passwords detected."))


class AgePanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Password Age", parent)
        self._chart = BarChartWidget()
        self._chart.setMinimumHeight(160)
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._chart.set_bars(
            [
                ("0-30", snapshot.age_0_30),
                ("30-90", snapshot.age_30_90),
                ("90-180", snapshot.age_90_180),
                ("180-365", snapshot.age_180_365),
                ("365+", snapshot.age_365_plus),
            ]
        )


class ExpiredPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Expired Passwords", parent)
        self._chart = BarChartWidget()
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._chart.set_bars(
            [
                (tr("Expired"), snapshot.expired_count),
                (tr("7d"), snapshot.expiring_7),
                (tr("30d"), snapshot.expiring_30),
                (tr("90d"), snapshot.expiring_90),
            ]
        )


class EntropyPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Entropy Analysis", parent)
        self._avg = KpiCard(tr("Average"))
        self._min = KpiCard(tr("Minimum"))
        self._max = KpiCard(tr("Maximum"))
        row = QHBoxLayout()
        row.addWidget(self._avg)
        row.addWidget(self._min)
        row.addWidget(self._max)
        self._body.addLayout(row)
        self._chart = BarChartWidget()
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._avg.set_value(f"{snapshot.entropy_avg:.0f}")
        self._min.set_value(f"{snapshot.entropy_min:.0f}")
        self._max.set_value(f"{snapshot.entropy_max:.0f}")
        self._chart.set_bars([(b.name, b.count) for b in snapshot.entropy_buckets])


class LengthPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Password Length Distribution", parent)
        self._chart = BarChartWidget()
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._chart.set_bars(
            [
                ("<8", snapshot.length_under_8),
                ("8-11", snapshot.length_8),
                ("12-15", snapshot.length_12),
                ("16-19", snapshot.length_16),
                ("20+", snapshot.length_20_plus),
            ]
        )


class CategoryPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Category Analysis", parent)
        self._chart = BarChartWidget()
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._chart.set_bars(
            [(c.name.title(), c.count) for c in snapshot.categories],
            horizontal=True,
        )


class OtpPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("OTP Analysis", parent)
        self._donut = DonutChartWidget()
        self._missing = KpiCard(tr("Critical without OTP"))
        self._body.addWidget(self._donut)
        self._body.addWidget(self._missing)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._donut.set_slices(
            [
                (tr("With OTP"), snapshot.otp_with),
                (tr("Without OTP"), snapshot.otp_without),
            ],
            center=str(snapshot.otp_with),
        )
        tone = "danger" if snapshot.otp_critical_missing else "success"
        self._missing.set_value(str(snapshot.otp_critical_missing), tone=tone)


class TagsPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Tags Analysis", parent)
        self._untagged = KpiCard(tr("Untagged"))
        self._chart = BarChartWidget()
        self._body.addWidget(self._untagged)
        self._body.addWidget(self._chart)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._untagged.set_value(str(snapshot.untagged))
        self._chart.set_bars(
            [(t.name, t.count) for t in snapshot.top_tags[:8]],
            horizontal=True,
        )


class UsernamePanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Username Analysis", parent)
        self._cards = [
            KpiCard(tr("Empty")),
            KpiCard(tr("Reused")),
            KpiCard(tr("Admin")),
            KpiCard(tr("Root")),
        ]
        row = QHBoxLayout()
        for card in self._cards:
            row.addWidget(card)
        self._body.addLayout(row)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._cards[0].set_value(str(snapshot.empty_usernames), tone="warning")
        self._cards[1].set_value(str(snapshot.reused_usernames))
        self._cards[2].set_value(str(snapshot.admin_usernames))
        self._cards[3].set_value(str(snapshot.root_usernames))


class UrlPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("URL Analysis", parent)
        self._donut = DonutChartWidget()
        self._body.addWidget(self._donut)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._donut.set_slices(
            [
                (tr("Empty"), snapshot.url_empty),
                ("HTTPS", snapshot.url_https),
                ("HTTP", snapshot.url_http),
                (tr("Other"), snapshot.url_other),
            ]
        )


class CertificatePanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Certificate Analysis", parent)
        self._cards = [
            KpiCard(tr("Total")),
            KpiCard(tr("Expired")),
            KpiCard(tr("Expiring soon")),
        ]
        row = QHBoxLayout()
        for card in self._cards:
            row.addWidget(card)
        self._body.addLayout(row)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._cards[0].set_value(str(snapshot.cert_total))
        self._cards[1].set_value(
            str(snapshot.cert_expired),
            tone="danger" if snapshot.cert_expired else "success",
        )
        self._cards[2].set_value(
            str(snapshot.cert_expiring_soon),
            tone="warning" if snapshot.cert_expiring_soon else "success",
        )


class SshPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("SSH Analysis", parent)
        self._donut = DonutChartWidget()
        self._enc = KpiCard(tr("Passphrase protected"))
        self._body.addWidget(self._donut)
        self._body.addWidget(self._enc)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._donut.set_slices(
            [
                ("RSA", snapshot.ssh_rsa),
                ("ED25519", snapshot.ssh_ed25519),
                ("ECDSA", snapshot.ssh_ecdsa),
                (tr("Other"), snapshot.ssh_other),
            ],
            center=str(snapshot.ssh_total),
        )
        enc_tone = (
            "success"
            if snapshot.ssh_encrypted == snapshot.ssh_total
            else "warning"
        )
        self._enc.set_value(
            f"{snapshot.ssh_encrypted}/{snapshot.ssh_total}",
            tone=enc_tone,
        )


class AttachmentsPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Attachments", parent)
        self._types = BarChartWidget()
        self._sizes = BarChartWidget()
        self._total = KpiCard(tr("Total files"))
        self._body.addWidget(self._total)
        row = QHBoxLayout()
        row.addWidget(self._types)
        row.addWidget(self._sizes)
        self._body.addLayout(row)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._total.set_value(str(snapshot.attachment_total))
        self._types.set_bars([(t.name, t.count) for t in snapshot.attachment_types[:8]])
        self._sizes.set_bars(
            [(b.name, b.count) for b in snapshot.attachment_size_buckets]
        )


class FavoritesPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Favorites", parent)
        self._fav = TimelineList()
        self._recent = TimelineList()
        self._body.addWidget(QLabel(tr("Tagged favorites")))
        self._body.addWidget(self._fav)
        self._body.addWidget(QLabel(tr("Recently accessed")))
        self._body.addWidget(self._recent)
        self._fav.list_widget.itemDoubleClicked.connect(self._on_fav)
        self._recent.list_widget.itemDoubleClicked.connect(self._on_recent)
        self._fav_refs: list[str] = []
        self._recent_refs: list[str] = []

    def _on_fav(self, item) -> None:
        row = self._fav.list_widget.row(item)
        if 0 <= row < len(self._fav_refs):
            self.entry_activated.emit(self._fav_refs[row])

    def _on_recent(self, item) -> None:
        row = self._recent.list_widget.row(item)
        if 0 <= row < len(self._recent_refs):
            self.entry_activated.emit(self._recent_refs[row])

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._fav_refs = [e.uuid for e in snapshot.favorite_entries]
        self._recent_refs = [e.uuid for e in snapshot.recently_accessed]
        fav_items = [
            f"{e.title} ({e.detail})" if e.detail else e.title
            for e in snapshot.favorite_entries
        ]
        self._fav.set_items(fav_items or [tr("No favorites tagged")])
        self._recent.set_items(
            [
                f"{e.title} · {e.detail}" if e.detail else e.title
                for e in snapshot.recently_accessed
            ]
            or [tr("No recent access data")]
        )


class DatabaseHealthPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Database Health", parent)
        self._cards = [
            KpiCard(tr("Groups")),
            KpiCard(tr("Entries")),
            KpiCard(tr("Attachments")),
            KpiCard(tr("OTP")),
            KpiCard(tr("Certificates")),
            KpiCard(tr("SSH keys")),
        ]
        row = QHBoxLayout()
        for card in self._cards:
            row.addWidget(card)
        self._body.addLayout(row)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        values = [
            snapshot.total_groups,
            snapshot.total_entries,
            snapshot.total_attachments,
            snapshot.total_otp,
            snapshot.total_certificates,
            snapshot.total_ssh_keys,
        ]
        for card, value in zip(self._cards, values, strict=True):
            card.set_value(str(value))


class RiskMatrixPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Risk Matrix", parent)
        self._heat = HeatMapWidget()
        self._heat.setMinimumHeight(110)
        self._body.addWidget(self._heat)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._heat.set_cells(
            [
                (tr("Critical"), snapshot.risk_critical, "critical"),
                (tr("High"), snapshot.risk_high, "high"),
                (tr("Medium"), snapshot.risk_medium, "medium"),
                (tr("Low"), snapshot.risk_low, "low"),
            ]
        )


class RecommendationsPanel(DashboardPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Recommendations", parent)
        self._list = TimelineList()
        self._body.addWidget(self._list)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._list.set_items(list(snapshot.recommendations))


class FindingsPanel(DashboardPanel):
    """Legacy findings browser with Fix next."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Findings", parent)
        self._snapshot: DashboardSnapshot | None = None
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([tr("Severity"), tr("Finding")])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSortingEnabled(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setUniformRowHeights(True)
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tree.itemDoubleClicked.connect(self._on_item)
        fix_btn = QPushButton(tr("Fix next"))
        fix_btn.clicked.connect(self._fix_next)
        open_btn = QPushButton(tr("Open entry"))
        open_btn.clicked.connect(self._open_current)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(fix_btn)
        row.addWidget(open_btn)
        self._body.addLayout(row)
        self._body.addWidget(self._tree, stretch=1)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._snapshot = snapshot
        self._tree.setSortingEnabled(False)
        self._tree.clear()
        order = {"critical": 0, "warning": 1, "info": 2}
        for finding in sorted(
            snapshot.findings, key=lambda f: order.get(f.severity, 3)
        ):
            item = QTreeWidgetItem([tr(finding.severity), finding.message])
            if finding.entry_uuid:
                item.setData(0, int(Qt.ItemDataRole.UserRole), finding.entry_uuid)
                item.setData(1, int(Qt.ItemDataRole.UserRole), finding.kind)
            self._tree.addTopLevelItem(item)
        self._tree.setSortingEnabled(True)

    def _on_item(self, item: QTreeWidgetItem, _column: int) -> None:
        uuid = item.data(0, int(Qt.ItemDataRole.UserRole))
        if uuid:
            self.entry_activated.emit(str(uuid))

    def _open_current(self) -> None:
        item = self._tree.currentItem()
        if item is not None:
            self._on_item(item, 0)

    def _fix_next(self) -> None:
        if self._snapshot is None:
            return
        priority = {"critical": 0, "warning": 1, "info": 2}
        actionable = [
            f
            for f in self._snapshot.findings
            if f.entry_uuid
            and f.kind
            in {
                "empty_password",
                "weak_password",
                "low_entropy",
                "pwned_password",
                "expired",
                "expiring_soon",
                "duplicate_password",
            }
        ]
        if not actionable:
            return
        actionable.sort(key=lambda f: priority.get(f.severity, 9))
        finding = actionable[0]
        assert finding.entry_uuid is not None
        self.fix_next_requested.emit(finding.kind, finding.entry_uuid)


def register_default_panels() -> None:
    """Idempotent registration of built-in panels."""
    from kdbxstudio.ui.security_dashboard.panel_registry import registered_panels

    if registered_panels():
        return
    register_panel("score", "Security Score", ScoreHeaderPanel, span=2)
    register_panel("password_stats", "Password Statistics", PasswordStatsPanel)
    register_panel("duplicates", "Duplicate Password Report", DuplicatesPanel)
    register_panel("age", "Password Age", AgePanel)
    register_panel("expired", "Expired Passwords", ExpiredPanel)
    register_panel("entropy", "Entropy Analysis", EntropyPanel)
    register_panel("length", "Password Length Distribution", LengthPanel)
    register_panel("category", "Category Analysis", CategoryPanel)
    register_panel("otp", "OTP Analysis", OtpPanel)
    register_panel("tags", "Tags Analysis", TagsPanel)
    register_panel("username", "Username Analysis", UsernamePanel)
    register_panel("url", "URL Analysis", UrlPanel)
    register_panel("certificate", "Certificate Analysis", CertificatePanel)
    register_panel("ssh", "SSH Analysis", SshPanel)
    register_panel("attachments", "Attachments", AttachmentsPanel)
    register_panel("favorites", "Favorites", FavoritesPanel)
    register_panel("db_health", "Database Health", DatabaseHealthPanel, span=2)
    register_panel("risk", "Risk Matrix", RiskMatrixPanel, span=2)
    register_panel("recommendations", "Recommendations", RecommendationsPanel)
    register_panel("findings", "Findings", FindingsPanel, span=2)