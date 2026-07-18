"""QSS builders — premium desktop depth via surfaces, borders, and soft elevation."""

from __future__ import annotations

from kdbxstudio.ui.theme.geometry import (
    RADIUS,
    SPACING,
    density_metrics,
    elevation_for,
    menu_metrics,
    type_scale_for_body,
)
from kdbxstudio.ui.theme.scale import UiScale
from kdbxstudio.ui.theme.tokens import ThemeTokens


def build_stylesheet(
    tokens: ThemeTokens,
    scale: UiScale | float | None = None,
    *,
    ui_density: str = "compact",
    font_size: int = 13,
    menu_size: str = "medium",
) -> str:
    t = tokens
    if isinstance(scale, UiScale):
        s = scale
    elif isinstance(scale, (int, float)):
        s = UiScale(float(scale))
    else:
        s = UiScale(1.0)

    dens = density_metrics(ui_density)
    menu = menu_metrics(menu_size)
    type_scale = type_scale_for_body(font_size)
    _ = elevation_for(t.appearance)

    def px(value: int | float) -> str:
        return f"{s.px(value)}px"

    body = s.font_px(type_scale.body)
    caption = s.font_px(type_scale.caption)
    display = s.font_px(type_scale.display)
    title = s.font_px(type_scale.title)
    menu_font = max(10, body + menu.font_delta)
    ctrl = dens.control_height
    row = dens.row_height
    r_sm = RADIUS.sm
    r_md = RADIUS.md
    r_lg = RADIUS.lg

    return f"""
* {{
  font-family: Inter, "Noto Sans", "DejaVu Sans", sans-serif;
  font-size: {body}px;
}}

QMainWindow, QDialog, QMessageBox {{
  background-color: {t.surface_app};
  color: {t.text_primary};
}}

QDialog {{
  border-radius: {px(r_lg)};
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
  border-radius: {px(r_md)};
  margin-top: {px(SPACING.sm)};
  padding-top: {px(SPACING.sm)};
  background-color: {t.surface_panel};
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  left: {px(SPACING.sm)};
  padding: 0 {px(SPACING.xs)};
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
  padding: 0 {px(SPACING.xs)};
  font-size: {menu_font}px;
  spacing: {px(2)};
  min-height: {px(menu.bar_height)};
}}

QMenuBar::item {{
  background: transparent;
  padding: {px(menu.item_pad_y // 2)} {px(menu.item_pad_x)};
  margin: {px(2)} 0;
  border-radius: {px(r_sm)};
}}

QMenuBar::item:selected, QMenuBar::item:pressed {{
  background-color: {t.surface_sunken};
}}

QMenu {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  border-radius: {px(r_md)};
  padding: {px(SPACING.xs)};
  font-size: {menu_font}px;
}}

QMenu::item {{
  padding: {px(menu.item_pad_y)} {px(SPACING.md)} {px(menu.item_pad_y)} {px(SPACING.sm)};
  border-radius: {px(r_sm)};
  min-height: {px(menu.item_min_height)};
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
  margin: {px(SPACING.xs)} {px(SPACING.sm)};
}}

QMenu::icon {{
  padding-left: {px(SPACING.xs)};
}}

QToolBar {{
  background-color: {t.surface_elevated};
  border-bottom: 1px solid {t.border_strong};
  spacing: {px(SPACING.sm)};
  padding: {px(SPACING.xs)} {px(SPACING.sm)};
  min-height: {px(ctrl)};
}}

QToolBar#mainToolbar {{
  background-color: {t.surface_elevated};
  border-bottom: 1px solid {t.border_strong};
}}

QToolBar::separator {{
  background: {t.border_subtle};
  width: 1px;
  margin: {px(SPACING.xs)} {px(SPACING.xs)};
}}

QToolButton, QPushButton {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_md)};
  padding: {px(SPACING.xs)} {px(12)};
  min-height: {px(ctrl - 8)};
  font-size: {body}px;
}}

QToolButton {{
  padding: {px(SPACING.xs)};
  min-width: {px(ctrl - 4)};
  min-height: {px(ctrl - 4)};
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

QPushButton[cssClass="secondary"] {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_strong};
}}

QPushButton[cssClass="ghost"] {{
  background-color: transparent;
  border: 1px solid transparent;
}}

QPushButton[cssClass="ghost"]:hover {{
  background-color: {t.surface_sunken};
  border-color: {t.border_subtle};
}}

QPushButton[cssClass="danger"] {{
  background-color: {t.text_danger};
  color: {t.brand_on_primary};
  border: 1px solid {t.text_danger};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser,
QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QDateTimeEdit {{
  background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_md)};
  padding: {px(SPACING.xs)} {px(SPACING.sm)};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
  font-size: {body}px;
  min-height: {px(ctrl - 8)};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QDateEdit:focus, QDateTimeEdit:focus {{
  border: 2px solid {t.focus_ring};
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
  border-radius: {px(r_md)};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
}}

QDateEdit::drop-down, QDateTimeEdit::drop-down {{
  subcontrol-origin: padding;
  subcontrol-position: center right;
  width: {px(22)};
  border: none;
  border-left: 1px solid {t.border_subtle};
  background-color: {t.surface_elevated};
  border-top-right-radius: {px(r_md)};
  border-bottom-right-radius: {px(r_md)};
}}

QDateEdit::drop-down:hover, QDateTimeEdit::drop-down:hover {{
  background-color: {t.surface_sunken};
}}

QDateEdit::down-arrow, QDateTimeEdit::down-arrow {{
  width: {px(10)};
  height: {px(10)};
}}

QCalendarWidget {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  border-radius: {px(r_md)};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
  background-color: {t.surface_panel};
  border-top-left-radius: {px(r_md)};
  border-top-right-radius: {px(r_md)};
  border-bottom: 1px solid {t.border_subtle};
  padding: {px(SPACING.xs)};
  min-height: {px(36)};
}}

QCalendarWidget QWidget {{
  alternate-background-color: {t.surface_sunken};
  background-color: {t.surface_elevated};
  color: {t.text_primary};
}}

QCalendarWidget QToolButton {{
  background-color: transparent;
  color: {t.text_primary};
  border: 1px solid transparent;
  border-radius: {px(r_sm)};
  padding: {px(SPACING.xs)} {px(SPACING.sm)};
  margin: 1px;
  font-size: {body}px;
  font-weight: 600;
}}

QCalendarWidget QToolButton:hover {{
  background-color: {t.surface_sunken};
  border-color: {t.border_subtle};
  color: {t.text_primary};
}}

QCalendarWidget QToolButton:pressed {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
}}

QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {{
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  qproperty-iconSize: {px(14)}px;
  min-width: {px(28)};
  max-width: {px(28)};
  min-height: {px(28)};
}}

QCalendarWidget QToolButton#qt_calendar_monthbutton,
QCalendarWidget QToolButton#qt_calendar_yearbutton {{
  color: {t.text_primary};
  font-weight: 600;
}}

QCalendarWidget QToolButton::menu-indicator {{
  image: none;
  width: 0;
}}

QCalendarWidget QSpinBox {{
  background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_sm)};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
}}

QCalendarWidget QMenu {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
}}

QCalendarWidget QMenu::item:selected {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
}}

QCalendarWidget QAbstractItemView {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
  outline: 0;
  border: none;
}}

QCalendarWidget QAbstractItemView:enabled {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  selection-background-color: {t.brand_primary};
  selection-color: {t.brand_on_primary};
}}

QCalendarWidget QAbstractItemView:disabled {{
  color: {t.text_muted};
}}

QCalendarWidget QWidget#qt_calendar_calendarview {{
  background-color: {t.surface_elevated};
  border-bottom-left-radius: {px(r_md)};
  border-bottom-right-radius: {px(r_md)};
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
  border-top-left-radius: {px(r_sm)};
  border-top-right-radius: {px(r_sm)};
  padding: {px(SPACING.xs + 2)} {px(SPACING.md)};
  margin-right: 1px;
  font-size: {body}px;
  min-height: {px(22)};
}}

QTabBar::tab:selected {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border-bottom: 2px solid {t.brand_primary};
}}

QTabBar::tab:hover:!selected {{
  color: {t.text_primary};
  background-color: {t.surface_elevated};
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
  border-bottom: 2px solid {t.brand_primary};
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
  padding: {px(SPACING.sm)} {px(SPACING.md)};
  text-align: left;
  font-weight: 600;
}}

QTreeWidget#groupTreePane {{
  border: none;
  border-radius: 0;
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_panel};
  show-decoration-selected: 1;
}}

QTreeWidget, QTableWidget, QListWidget,
QTreeView, QTableView, QListView, QAbstractItemView {{
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: none;
  border-radius: {px(r_md)};
  gridline-color: transparent;
  font-size: {body}px;
  outline: 0;
  selection-background-color: {t.surface_elevated};
  selection-color: {t.text_primary};
}}

QTableView#entryListPane {{
  border: none;
  border-radius: 0;
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_sunken};
}}

QAbstractItemView:focus {{
  border: none;
  outline: none;
}}

QTableView#entryListPane:focus {{
  border: none;
  outline: none;
}}

QTreeWidget#groupTreePane:focus {{
  border: none;
  outline: none;
}}

QHeaderView {{
  background-color: transparent;
}}

QHeaderView::section {{
  background-color: {t.surface_elevated};
  color: {t.text_secondary};
  border: none;
  padding: {px(SPACING.sm)} {px(SPACING.md)};
  font-size: {caption}px;
  font-weight: 600;
}}

QTreeWidget::item, QTableWidget::item, QListWidget::item,
QTreeView::item, QTableView::item, QListView::item {{
  min-height: {px(row - 4)};
  padding: {px(SPACING.xs)} {px(SPACING.md)};
  color: {t.text_primary};
  border: none;
  border-radius: {px(r_sm)};
  margin: 1px {px(SPACING.xs)};
}}

QTreeWidget::item:hover, QTableWidget::item:hover, QListWidget::item:hover,
QTreeView::item:hover, QTableView::item:hover, QListView::item:hover {{
  background-color: {t.surface_sunken};
  color: {t.text_primary};
}}

QTreeWidget::item:selected, QTableWidget::item:selected, QListWidget::item:selected,
QTreeView::item:selected, QTableView::item:selected, QListView::item:selected,
QAbstractItemView::item:selected {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: none;
}}

QTreeWidget::item:selected:active, QTableView::item:selected:active,
QTableWidget::item:selected:active, QListWidget::item:selected:active {{
  background-color: {t.surface_elevated};
  color: {t.brand_primary};
  border: none;
}}

QTreeWidget::item:selected:!active, QTableView::item:selected:!active {{
  background-color: {t.surface_sunken};
  color: {t.text_primary};
}}

QSplitter::handle {{
  background-color: {t.surface_sunken};
}}

QSplitter::handle:hover {{
  background-color: {t.brand_accent};
}}

QSplitter::handle:horizontal {{
  width: {px(SPACING.xs)};
  margin: 0;
}}

QSplitter::handle:vertical {{
  height: {px(SPACING.xs)};
  margin: 0;
}}

QSplitter#workspaceSplitter::handle:horizontal {{
  width: {px(SPACING.xs)};
  background-color: {t.surface_sunken};
}}

QStatusBar {{
  background-color: {t.surface_elevated};
  color: {t.text_secondary};
  border-top: 1px solid {t.border_strong};
  font-size: {caption}px;
  min-height: {px(22)};
  max-height: {px(26)};
}}

QProgressBar {{
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_sm)};
  text-align: center;
  color: {t.text_primary};
  max-height: {px(10)};
}}

QProgressBar::chunk {{
  background-color: {t.brand_primary};
  border-radius: {px(r_sm - 1)};
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
  spacing: {px(SPACING.sm)};
  color: {t.text_primary};
  font-size: {body}px;
  background-color: transparent;
}}

QCheckBox:disabled, QRadioButton:disabled {{
  color: {t.text_muted};
}}

QScrollBar:vertical {{
  background: {t.surface_sunken};
  width: {px(10)};
  margin: 0;
  border: none;
}}

QScrollBar::handle:vertical {{
  background: {t.border_strong};
  border-radius: {px(r_sm)};
  min-height: {px(24)};
}}

QScrollBar::handle:vertical:hover {{
  background: {t.brand_primary};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0;
}}

QScrollBar:horizontal {{
  background: {t.surface_sunken};
  height: {px(10)};
  margin: 0;
  border: none;
}}

QScrollBar::handle:horizontal {{
  background: {t.border_strong};
  border-radius: {px(r_sm)};
  min-width: {px(24)};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
  width: 0;
}}

QToolTip {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_strong};
  border-radius: {px(r_sm)};
  padding: {px(SPACING.xs)} {px(SPACING.sm)};
  font-size: {caption}px;
}}

QToolButton[cssClass="chip"] {{
  border-radius: {px(r_lg)};
  padding: {px(SPACING.xs)} {px(12)};
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  color: {t.text_secondary};
  font-size: {caption}px;
  min-height: {px(24)};
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
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_lg)};
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

QLabel#emptyTitle {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QLabel#dialogTitle {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QLabel#dialogSubtitle {{
  color: {t.text_secondary};
  font-size: {caption}px;
}}

QLabel#totpCode {{
  font-family: "JetBrains Mono", "Ui Mono", "DejaVu Sans Mono", monospace;
  font-size: {s.font_px(22)}px;
  font-weight: 600;
  color: {t.text_primary};
  letter-spacing: 2px;
}}

QLabel#auditSummaryStrip {{
  color: {t.text_secondary};
  padding: {px(SPACING.sm)} {px(SPACING.md)};
  background-color: {t.surface_sunken};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_md)};
  font-size: {caption}px;
}}

QWidget#securityDashboard {{
  background-color: {t.surface_app};
}}

QFrame#securityDashboardPanel {{
  background-color: {t.surface_panel};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_lg)};
}}

QFrame#securityDashboardPanel:hover {{
  border-color: {t.border_strong};
}}

QLabel#securityPanelTitle {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QWidget#securityKpiCard {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_md)};
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
  border-radius: {px(r_sm)};
  padding: 2px {px(SPACING.sm)};
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
  border-radius: {px(r_md)};
}}

QLabel#entryKindBadge {{
  background-color: {t.surface_sunken};
  color: {t.text_secondary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_sm)};
  padding: 1px {px(SPACING.sm)};
  font-size: {caption}px;
}}

QLabel#breadcrumbPath {{
  color: {t.text_muted};
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

QWidget#accentSwatch {{
  border: 2px solid transparent;
  border-radius: {px(r_md)};
  min-width: {px(28)};
  min-height: {px(28)};
  max-width: {px(28)};
  max-height: {px(28)};
}}

QWidget#accentSwatch[selected="true"] {{
  border-color: {t.text_primary};
}}

QLabel#expiryChip, QLabel#statusChip, QLabel#toastBanner {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(r_lg)};
  padding: {px(SPACING.xs)} {px(SPACING.md)};
  font-size: {caption}px;
  font-weight: 600;
}}

QLabel#expiryChip[tone="danger"], QLabel#statusChip[tone="danger"],
QLabel#toastBanner[tone="danger"] {{
  background-color: {t.surface_sunken};
  color: {t.text_danger};
  border-color: {t.text_danger};
}}

QLabel#expiryChip[tone="warning"], QLabel#statusChip[tone="warning"],
QLabel#toastBanner[tone="warning"] {{
  background-color: {t.surface_sunken};
  color: {t.text_warning};
  border-color: {t.text_warning};
}}

QLabel#expiryChip[tone="success"], QLabel#statusChip[tone="success"],
QLabel#toastBanner[tone="success"] {{
  background-color: {t.surface_sunken};
  color: {t.text_success};
  border-color: {t.text_success};
}}

QLabel#tagChip {{
  border-radius: {px(r_sm)};
  padding: 2px {px(SPACING.sm)};
  font-size: {caption}px;
}}

QWidget#emptyState QLabel#emptyStateTitle {{
  color: {t.text_primary};
  font-size: {title}px;
  font-weight: 600;
}}

QWidget#emptyState QLabel#emptyStateHint {{
  color: {t.text_muted};
  font-size: {caption}px;
}}

QTableView#entryListPane::item:hover,
QTreeView::item:hover {{
  background-color: {t.surface_elevated};
}}

QTableView#entryListPane:focus,
QTreeView:focus,
QListWidget:focus {{
  outline: none;
  border: 1px solid {t.focus_ring};
}}

QWidget#filterChip:hover, QPushButton[cssClass="chip"]:hover {{
  background-color: {t.surface_elevated};
  border-color: {t.brand_primary};
}}

QFrame#securityPanel:hover {{
  border-color: {t.border_strong};
  background-color: {t.surface_elevated};
}}
"""
