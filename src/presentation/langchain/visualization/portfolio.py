"""
Визуализация структуры портфеля - Sunburst диаграмма.
"""

import plotly.express as px
import pandas as pd
from typing import List, Dict, Any
from .utils import get_sector_by_ticker, safe_float, format_currency


def create_portfolio_sunburst(positions: List[Dict[str, Any]]) -> str:
    """
    Создает Sunburst диаграмму распределения активов по секторам экономики.

    Диаграмма показывает:
    - Внешнее кольцо: секторы экономики
    - Внутреннее кольцо: конкретные инструменты
    - Размер сегмента: текущая стоимость позиции
    - Цвет: доходность позиции (зеленый - прибыль, красный - убыток)

    Args:
        positions: Список позиций из AccountDTO.positions

    Returns:
        JSON-строка с графиком Plotly для отображения в Streamlit

    Example:
        >>> positions = [
        ...     {
        ...         "symbol": "SBER@TQBR",
        ...         "quantity": {"value": "100"},
        ...         "current_price": {"value": "250.5"},
        ...         "unrealized_pnl": {"value": "1500"}
        ...     }
        ... ]
        >>> fig_json = create_portfolio_sunburst(positions)
    """
    if not positions:
        # Создаем пустую диаграмму с сообщением
        fig = px.sunburst(
            pd.DataFrame([{"Сектор": "Нет данных", "value": 1}]),
            path=["Сектор"],
            values="value",
            title="Портфель пуст"
        )
        return fig.to_json()

    # Преобразуем данные в DataFrame с иерархией
    data = []
    for pos in positions:
        symbol = pos.get("symbol", "UNKNOWN")
        ticker = symbol.split("@")[0]
        sector = get_sector_by_ticker(symbol)

        # Извлекаем числовые значения
        quantity = safe_float(pos.get("quantity", {}))
        current_price = safe_float(pos.get("current_price", {}))
        unrealized_pnl = safe_float(pos.get("unrealized_pnl", {}))

        # Рассчитываем текущую стоимость и доходность
        current_value = current_price * quantity

        if current_value > 0:
            pnl_percent = (unrealized_pnl / (current_value - unrealized_pnl)) * \
                100 if (current_value - unrealized_pnl) != 0 else 0

            data.append({
                "Сектор": sector,
                "Инструмент": ticker,
                "Стоимость": current_value,
                "Доходность": pnl_percent,
                "PnL": unrealized_pnl,
                "Количество": quantity,
                "Цена": current_price,
            })

    if not data:
        # Если после фильтрации данных нет
        fig = px.sunburst(
            pd.DataFrame([{"Сектор": "Нет активных позиций", "value": 1}]),
            path=["Сектор"],
            values="value",
            title="Нет активных позиций"
        )
        return fig.to_json()

    df = pd.DataFrame(data)

    # Создаем Sunburst диаграмму
    fig = px.sunburst(
        df,
        path=["Сектор", "Инструмент"],
        values="Стоимость",
        color="Доходность",
        color_continuous_scale=[
            [0, "rgb(220, 50, 50)"],      # Красный для убытков
            [0.5, "rgb(240, 240, 240)"],  # Серый для нуля
            [1, "rgb(50, 200, 50)"]       # Зеленый для прибыли
        ],
        color_continuous_midpoint=0,
        hover_data={
            "Стоимость": ":,.0f",
            "Доходность": ":.2f",
            "PnL": ":,.0f",
            "Количество": ":,.0f",
            "Цена": ":,.2f",
        },
        title="Структура портфеля по секторам экономики"
    )

    # Настройка внешнего вида
    fig.update_traces(
        textinfo="label+percent parent",
        hovertemplate="<b>%{label}</b><br>" +
                      "Стоимость: %{value:,.0f} ₽<br>" +
                      "Доля: %{percentParent:.1%}<br>" +
                      "Доходность: %{customdata[1]:.2f}%<br>" +
                      "P&L: %{customdata[2]:,.0f} ₽<br>" +
                      "<extra></extra>"
    )

    fig.update_layout(
        margin=dict(t=50, l=0, r=0, b=0),
        height=600,
        font=dict(size=12),
        coloraxis_colorbar=dict(
            title="Доходность, %",
            ticksuffix="%"
        )
    )

    return fig.to_json()
