"""QSS builders — compact, calm desktop chrome."""

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

    return f"""
* {{
  font-family: Inter, "Noto Sans", "DejaVu Sans", sans-serif;
  font-size: {body}px;
}}

QMainWindow, QDialog {{
  background-color: {t.surface_app};
  color: {t.text_primary};
}}

QWidget {{
  color: {t.text_primary};
  background-color: transparent;
}}

QMenuBar {{
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border-bottom: 1px solid {t.border_subtle};
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
  background-color: {t.surface_panel};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
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

QMenu::separator {{
  height: 1px;
  background: {t.border_subtle};
  margin: {px(3)} {px(4)};
}}

QToolBar {{
  background-color: {t.surface_panel};
  border-bottom: 1px solid {t.border_subtle};
  spacing: {px(4)};
  padding: {px(4)};
  min-height: {px(36)};
}}

QToolButton, QPushButton {{
  background-color: {t.surface_elevated};
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

QPushButton:default, QPushButton[cssClass="primary"] {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
  border: 1px solid {t.brand_primary};
}}

QPushButton:default:hover {{
  background-color: {t.brand_primary_hover};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
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

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QComboBox:focus {{
  border: 1px solid {t.focus_ring};
}}

QTabWidget::pane {{
  border: 1px solid {t.border_subtle};
  background-color: {t.surface_panel};
  border-radius: {px(4)};
  top: -1px;
}}

QTabBar::tab {{
  background-color: {t.surface_sunken};
  color: {t.text_secondary};
  border: 1px solid {t.border_subtle};
  border-bottom: none;
  border-top-left-radius: {px(4)};
  border-top-right-radius: {px(4)};
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

QDockWidget {{
  color: {t.text_primary};
  titlebar-close-icon: none;
  font-size: {body}px;
}}

QDockWidget::title {{
  background-color: {t.surface_panel};
  border: 1px solid {t.border_subtle};
  padding: {px(3)} {px(5)};
}}

QTreeWidget, QTableWidget, QListWidget {{
  background-color: {t.surface_panel};
  alternate-background-color: {t.surface_sunken};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
  border-radius: {px(4)};
  gridline-color: {t.border_subtle};
  font-size: {body}px;
}}

QHeaderView::section {{
  background-color: {t.surface_elevated};
  color: {t.text_secondary};
  border: none;
  border-bottom: 1px solid {t.border_subtle};
  padding: {px(3)} {px(5)};
  font-size: {caption}px;
}}

QTreeWidget::item, QTableWidget::item, QListWidget::item {{
  min-height: {px(20)};
  padding: 1px {px(3)};
}}

QTreeWidget::item:selected, QTableWidget::item:selected, QListWidget::item:selected {{
  background-color: {t.brand_primary};
  color: {t.brand_on_primary};
}}

QStatusBar {{
  background-color: {t.surface_panel};
  color: {t.text_secondary};
  border-top: 1px solid {t.border_subtle};
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

QCheckBox {{
  spacing: {px(4)};
  color: {t.text_primary};
  font-size: {body}px;
}}

QScrollBar:vertical {{
  background: {t.surface_sunken};
  width: {px(8)};
  margin: 0;
}}

QScrollBar::handle:vertical {{
  background: {t.border_strong};
  border-radius: {px(4)};
  min-height: {px(16)};
}}

QToolTip {{
  background-color: {t.surface_elevated};
  color: {t.text_primary};
  border: 1px solid {t.border_subtle};
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

QWidget#unlockCard, QWidget#emptyCard {{
  background-color: {t.surface_elevated};
  border: 1px solid {t.border_subtle};
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
  padding: {px(3)} {px(5)};
  background-color: {t.surface_sunken};
  border-radius: {px(4)};
  font-size: {caption}px;
}}
"""
