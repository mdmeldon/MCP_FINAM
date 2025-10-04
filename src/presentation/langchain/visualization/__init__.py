"""
Модуль визуализации для Streamlit приложения.

Содержит функции для создания интерактивных графиков с помощью Plotly:
- portfolio: Sunburst диаграмма структуры портфеля по секторам
- trades: График котировок с иконками сделок
- performance: Кривая доходности и метрики стратегии, сравнение с бенчмарком
- rebalancing: Симуляция ребалансировки портфеля с целевыми весами
"""

from .portfolio import create_portfolio_sunburst
from .trades import create_trades_chart
from .performance import create_performance_chart, create_portfolio_performance_chart
from .rebalancing import (
    create_rebalancing_table,
    create_rebalancing_comparison_chart,
    calculate_target_weights,
)
from .utils import get_sector_by_ticker, calculate_pnl

__all__ = [
    "create_portfolio_sunburst",
    "create_trades_chart",
    "create_performance_chart",
    "create_portfolio_performance_chart",
    "create_rebalancing_table",
    "create_rebalancing_comparison_chart",
    "calculate_target_weights",
    "get_sector_by_ticker",
    "calculate_pnl",
]
