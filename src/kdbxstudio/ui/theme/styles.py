"""QSS builders — KeePassXC-like pane depth via borders and surface steps."""

from __future__ import annotations

from kdbxstudio.ui.theme.scale import UiScale
from kdbxstudio.ui.theme.tokens import ThemeTokens


def build_stylesheet(
    tokens: ThemeTokens,
    scale: UiScale | float | None = None,
) -> str:
    t = tokens
    if isinstance(scale, UiScale):
        s = scale
    elif isinstance(scale, (int, float)):
        s = UiScale(float(scale))
    else:
        s = UiScale(1.0)

    def px(value: int | float) -> str:
        return f"{s.px(value)}px"

    body = s.font_px(11)
    caption = s.font_px(10)
    display = s.font_px(18)
    title = s.font_px(14)

    return f"""
* {{
  font-family: Inter, "Noto Sans", "DejaVu Sans", sans-serif;
  font-size: {body}px;
}}

QMainWindow, QDialog, QMessageBox {{
  background-color: {t.surface_app};
  color: {t.text_primary};
}}

QMainWindow::separator {{
  background: {t.border_strong};
  width: 1px;
  height: 1px;
}}

QWidget {{
  color: {t.text_primary};
}}

QAbstractScrollArea {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
}}

QFrame, QGroupBox {{
  color: {t.text_primary};
}}

QGroupBox {{
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  margin-top: {px(8)};
  padding-top: {px(6)};
  background-color: {t.surface_panel};
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  left: {px(8)};
  padding: 0 {px(4)};
  color: {t.text_secondary};
}}

QLabel {{
  background-color: transparent;
  color: {t.text_primary};
}}

QMenuBar {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border-bottom: 1px solid {t.border_strong};
  padding: 0 {px(2)};
  font-size: {body}px;
  spacing: 0;
  min-height: {px(24)};
}}

QMenuBar::item {{
  background: transparent;
  padding: {px(3)} {px(7)};
  margin: 0;
  border-radius: {px(3)};
}}

QMenuBar::item:selected, QMenuBar::item:pressed {{
  background-color: {t.surface_sunken};
}}

QMenu {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  padding: {px(3)};
  font-size: {body}px;
}}

QMenu::item {{
  padding: {px(3)} {px(16)} {px(3)} {px(8)};
  border-radius: {px(3)};
  min-height: {px(18)};
}}

QMenu::item:selected {{
  background-color: {t.surface_sunken};
}}

QMenu::item:disabled {{
  color: {t.text_muted};
}}

QMenu::separator {{
  height: 1px;
  background: {t.border_subtle};
  margin: {px(3)} {px(4)};
}}

QToolBar {{
  background-color: {t.surface_elevated};
  border-bottom: 1px solid {t.border_strong};
  spacing: {px(4)};
  padding: {px(4)};
  min-height: {px(36)};
}}

QToolBar#mainToolbar {{
  background-color: {t.surface_elevated};
  border-bottom: 1px solid {t.border_strong};
}}

QToolButton, QPushButton {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  padding: {px(3)} {px(7)};
  min-height: {px(16)};
  font-size: {body}px;
}}

QPushButton:hover, QToolButton:hover {{
  border-color: {t.brand_primary};
  background-color: {t.surface_sunken};
}}

QPushButton:pressed, QToolButton:pressed {{
  background-color: {t.surface_sunken};
}}

QPushButton:disabled, QToolButton:disabled {{
  color: {t.text_muted};
  background-color: {t.surface_sunken};
  border-color: {t.border_subtle};
}}

QPushButton:default, QPushButton[cssClass="primary"] {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
  border: 1px solid {t.brand_primary};
}}

QPushButton:default:hover, QPushButton[cssClass="primary"]:hover {{
  background-color: {t.brand_primary_hover};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser,
QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QDateTimeEdit {{
  background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  padding: {px(3)} {px(5)};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
  font-size: {body}px;
  min-height: {px(20)};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QDateEdit:focus, QDateTimeEdit:focus {{
  border: 1px solid {t.focus_ring};
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
QSpinBox:disabled, QComboBox:disabled, QDateEdit:disabled {{
  color: {t.text_muted};
  background-color: {t.surface_panel};
}}

QComboBox QAbstractItemView {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
}}

QCalendarWidget {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
}}

QCalendarWidget QWidget {{
  alternate-background-color: {t.surface_sunken};
}}

QCalendarWidget QToolButton {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
}}

QCalendarWidget QAbstractItemView:enabled {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
}}

QTabWidget::pane {{
  border: 1px solid {t.border_subtle};
  background-color: {t.surface_panel};
  border-radius: 0;
  top: -1px;
}}

QTabBar::tab {{
  background-color: {t.surface_sunken};
  color: {t.text_secondary};
  border: 1px solid {t.border_subtle};
  border-bottom: none;
  border-top-left-radius: {px(3)};
  border-top-right-radius: {px(3)};
  padding: {px(3)} {px(8)};
  margin-right: 1px;
  font-size: {body}px;
  min-height: {px(18)};
}}

QTabBar::tab:selected {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border-bottom: 2px solid {t.brand_accent};
}}

QTabBar::tab:disabled {{
  color: {t.text_muted};
}}

QTabWidget#dbTabs::pane {{
  border: none;
  background-color: transparent;
  top: 0;
}}

QTabWidget#dbTabs QTabBar::tab {{
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-bottom: none;
}}

QTabWidget#dbTabs QTabBar::tab:selected {{
  background-color: {t.surface_panel};
  border-bottom: 2px solid {t.brand_primary};
}}

QTabWidget#entryDetailPane::pane {{
  border: 1px solid {t.border_strong};
  border-left: none;
  background-color: {t.surface_elevated};
  border-radius: 0;
}}

QTabWidget#entryDetailPane QTabBar::tab:selected {{
  background-color: {t.surface_elevated};
}}

QDockWidget {{
  color: {t.text_primary};
  titlebar-close-icon: none;
  font-size: {body}px;
  border: 1px solid {t.border_strong};
}}

QDockWidget::title {{
  background-color: {t.surface_elevated};
  border: none;
  border-bottom: 1px solid {t.border_strong};
  padding: {px(4)} {px(6)};
  text-align: left;
}}

QTreeWidget#groupTreePane {{
  border: none;
  border-radius: 0;
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_sunken};
}}

QTreeWidget, QTableWidget, QListWidget,
QTreeView, QTableView, QListView, QAbstractItemView {{
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: 0;
  gridline-color: {t.border_subtle};
  font-size: {body}px;
  outline: 0;
}}

QTableView#entryListPane {{
  border: 1px solid {t.border_strong};
  border-right: none;
  border-radius: 0;
  background-color: {t.surface_panel};
}}

QAbstractItemView:focus {{
  border: 1px solid {t.focus_ring};
}}

QTableView#entryListPane:focus {{
  border: 1px solid {t.focus_ring};
  border-right: none;
}}

QTreeWidget#groupTreePane:focus {{
  border: none;
  outline: 1px solid {t.focus_ring};
}}

QHeaderView::section {{
  background-color: {t.surface_elevated};
  color: {t.text_secondary};
  border: none;
  border-right: 1px solid {t.border_subtle};
  border-bottom: 1px solid {t.border_strong};
  padding: {px(4)} {px(5)};
  font-size: {caption}px;
}}

QTreeWidget::item, QTableWidget::item, QListWidget::item,
QTreeView::item, QTableView::item, QListView::item {{
  min-height: {px(20)};
  padding: 1px {px(3)};
  color: {t.text_primary};
}}

QTreeWidget::item:selected, QTableWidget::item:selected, QListWidget::item:selected,
QTreeView::item:selected, QTableView::item:selected, QListView::item:selected,
QAbstractItemView::item:selected {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
}}

QTreeWidget::item:hover, QTableWidget::item:hover, QListWidget::item:hover,
QTreeView::item:hover, QTableView::item:hover, QListView::item:hover {{
  background-color: {t.surface_sunken};
}}

QSplitter::handle {{
  background-color: {t.border_strong};
}}

QSplitter::handle:hover {{
  background-color: {t.brand_primary};
}}

QSplitter::handle:horizontal {{
  width: 3px;
  margin: 0;
}}

QSplitter::handle:vertical {{
  height: 3px;
  margin: 0;
}}

QSplitter#workspaceSplitter::handle:horizontal {{
  width: 3px;
  background-color: {t.border_strong};
}}

QStatusBar {{
  background-color: {t.surface_elevated};
  color: {t.text_secondary};
  border-top: 1px solid {t.border_strong};
  font-size: {caption}px;
  min-height: {px(18)};
  max-height: {px(22)};
}}

QProgressBar {{
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  text-align: center;
  color: {t.text_primary};
  max-height: {px(10)};
}}

QProgressBar::chunk {{
  background-color: {t.brand_accent};
  border-radius: {px(3)};
}}

QProgressBar[tone="success"]::chunk {{
  background-color: {t.text_success};
}}

QProgressBar[tone="warning"]::chunk {{
  background-color: {t.text_warning};
}}

QProgressBar[tone="danger"]::chunk {{
  background-color: {t.text_danger};
}}

QProgressBar[tone="accent"]::chunk {{
  background-color: {t.brand_accent};
}}

QCheckBox, QRadioButton {{
  spacing: {px(4)};
  color: {t.text_primary};
  font-size: {body}px;
  background-color: transparent;
}}

QCheckBox:disabled, QRadioButton:disabled {{
  color: {t.text_muted};
}}

QScrollBar:vertical {{
  background: {t.surface_sunken};
  width: {px(8)};
  margin: 0;
  border: none;
}}

QScrollBar::handle:vertical {{
  background: {t.border_strong};
  border-radius: {px(4)};
  min-height: {px(16)};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0;
}}

QScrollBar:horizontal {{
  background: {t.surface_sunken};
  height: {px(8)};
  margin: 0;
  border: none;
}}

QScrollBar::handle:horizontal {{
  background: {t.border_strong};
  border-radius: {px(4)};
  min-width: {px(16)};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
  width: 0;
}}

QToolTip {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  padding: {px(3)} {px(5)};
  font-size: {caption}px;
}}

QToolButton[cssClass="chip"] {{
  border-radius: {px(8)};
  padding: 1px {px(6)};
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  color: {t.text_secondary};
  font-size: {caption}px;
}}

QToolButton[cssClass="chip"]:checked {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
  border-color: {t.brand_primary};
}}

QToolButton[cssClass="chip"]:hover {{
  border-color: {t.brand_primary};
}}

QWidget#workspaceRoot {{
  background-color: {t.surface_app};
}}

QWidget#workspaceChrome {{
  background-color: {t.surface_elevated};
  border-bottom: 1px solid {t.border_strong};
}}

QWidget#unlockCard, QWidget#emptyCard {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_strong};
  border-radius: {px(8)};
  max-width: {px(420)};
}}

QWidget#emptyWorkspace {{
  background-color: {t.surface_app};
}}

QLabel#emptyBrand {{
  color: {t.brand_primary};
  font-size: {display}px;
  font-weight: 600;
}}

QLabel#emptySubtitle {{
  color: {t.text_secondary};
  font-size: {body}px;
}}

QLabel#auditSummaryStrip {{
  color: {t.text_secondary};
  padding: {px(4)} {px(6)};
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  font-size: {caption}px;
}}

QWidget#securityDashboard {{
  background-color: {t.surface_app};
}}

QFrame#securityDashboardPanel {{
  background-color: {t.surface_panel};
  border: 1px solid {t.border_subtle};
  border-radius: {px(8)};
}}

QLabel#securityPanelTitle {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QWidget#securityKpiCard {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_subtle};
  border-radius: {px(6)};
}}

QLabel#securityKpiTitle {{
  color: {t.text_muted};
  font-size: {caption}px;
  font-weight: 500;
}}

QLabel#securityKpiValue {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QLabel#securityKpiValue[tone="success"] {{
  color: {t.text_success};
}}

QLabel#securityKpiValue[tone="warning"] {{
  color: {t.text_warning};
}}

QLabel#securityKpiValue[tone="danger"] {{
  color: {t.text_danger};
}}

QLabel#securityKpiSubtitle {{
  color: {t.text_secondary};
  font-size: {caption}px;
}}

QLabel#securityStatusBadge {{
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  padding: 2px {px(8)};
  font-size: {caption}px;
  font-weight: 600;
}}

QLabel#securityStatusBadge[tone="success"] {{
  color: {t.text_success};
}}

QLabel#securityStatusBadge[tone="warning"] {{
  color: {t.text_warning};
}}

QLabel#securityStatusBadge[tone="danger"] {{
  color: {t.text_danger};
}}

QLabel#securityPanelHint {{
  color: {t.text_secondary};
  font-size: {caption}px;
}}

QListWidget#securityTimelineList {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
}}

QLabel#entryKindBadge {{
  background-color: {t.surface_sunken};
  color: {t.text_secondary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  padding: 1px {px(6)};
  font-size: {caption}px;
}}

QLabel[tone="danger"] {{
  color: {t.text_danger};
  font-weight: bold;
}}

QLabel[tone="warning"] {{
  color: {t.text_warning};
  font-weight: bold;
}}

QLabel[tone="success"] {{
  color: {t.text_success};
}}

QLabel[tone="muted"] {{
  color: {t.text_muted};
}}

QLabel[tone="secondary"] {{
  color: {t.text_secondary};
  font-size: {caption}px;
}}
"""
