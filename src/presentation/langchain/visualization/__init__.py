"""
Модуль визуализации для Streamlit приложения.

Содержит функции для создания интерактивных графиков с помощью Plotly:
- portfolio: Sunburst диаграмма структуры портфеля по секторам
- trades: График котировок с иконками сделок
- performance: Кривая доходности и метрики стратегии
"""

from .portfolio import create_portfolio_sunburst
from .trades import create_trades_chart
from .performance import create_performance_chart
from .utils import get_sector_by_ticker, calculate_pnl

__all__ = [
    "create_portfolio_sunburst",
    "create_trades_chart",
    "create_performance_chart",
    "get_sector_by_ticker",
    "calculate_pnl",
]
