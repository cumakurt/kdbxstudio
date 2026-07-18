"""Smoke tests for Security Dashboard chart widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from kdbxstudio.ui.charts import (
    BarChartWidget,
    DonutChartWidget,
    GaugeWidget,
    HeatMapWidget,
    KpiCard,
)


def test_chart_widgets_construct(qapp: QApplication) -> None:
    gauge = GaugeWidget()
    gauge.set_data(92, label="Excellent")
    gauge.resize(200, 200)
    gauge.show()
    qapp.processEvents()

    donut = DonutChartWidget()
    donut.set_slices([("Strong", 5), ("Weak", 2)], center="7")
    donut.resize(240, 180)
    donut.show()
    qapp.processEvents()

    bars = BarChartWidget()
    bars.set_bars([("A", 3), ("B", 7)])
    bars.resize(240, 160)
    bars.show()
    qapp.processEvents()

    heat = HeatMapWidget()
    heat.set_cells([("Critical", 1, "critical"), ("Low", 4, "low")])
    heat.resize(320, 100)
    heat.show()
    qapp.processEvents()

    kpi = KpiCard("Entries")
    kpi.set_value("42", tone="success")
    kpi.show()
    qapp.processEvents()
