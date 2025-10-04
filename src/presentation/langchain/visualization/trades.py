"""
Визуализация графика сделок на истории с иконками входов/выходов.
"""

import plotly.graph_objects as go
from typing import List, Dict, Any
from datetime import datetime
from .utils import safe_float


def create_trades_chart(bars: List[Dict[str, Any]], trades: List[Dict[str, Any]]) -> str:
    """
    Создает график котировок с наложенными иконками сделок (входов/выходов).

    График отображает:
    - Линию цены закрытия по историческим барам
    - Зеленые треугольники вверх (🔺) для точек входа (покупок)
    - Красные треугольники вниз (🔻) для точек выхода (продаж)
    - Интерактивные подсказки с деталями сделок

    Args:
        bars: Исторические данные из BarsRespDTO.bars
        trades: Список сделок с информацией о side, price, timestamp

    Returns:
        JSON-строка с графиком Plotly

    Example:
        >>> bars = [
        ...     {
        ...         "timestamp": "2024-01-01T10:00:00Z",
        ...         "close": {"value": "100.5"},
        ...         "high": {"value": "101"},
        ...         "low": {"value": "99.5"}
        ...     }
        ... ]
        >>> trades = [
        ...     {
        ...         "timestamp": "2024-01-01T10:00:00Z",
        ...         "side": "SIDE_BUY",
        ...         "price": {"value": "100.5"}
        ...     }
        ... ]
        >>> fig_json = create_trades_chart(bars, trades)
    """
    fig = go.Figure()

    if not bars:
        # Пустой график с сообщением
        fig.add_annotation(
            text="Нет исторических данных для отображения",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title="График сделок на истории")
        return fig.to_json()

    # Извлекаем данные из баров
    dates = []
    closes = []
    highs = []
    lows = []
    volumes = []

    for bar in bars:
        try:
            timestamp = bar.get("timestamp")
            if isinstance(timestamp, str):
                dates.append(datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")))
            else:
                dates.append(timestamp)

            closes.append(safe_float(bar.get("close", {})))
            highs.append(safe_float(bar.get("high", {})))
            lows.append(safe_float(bar.get("low", {})))
            volumes.append(safe_float(bar.get("volume", {})))
        except (ValueError, TypeError) as e:
            continue

    # Основная линия цен
    fig.add_trace(go.Scatter(
        x=dates,
        y=closes,
        mode="lines",
        name="Цена закрытия",
        line=dict(color="rgb(50, 120, 200)", width=2),
        hovertemplate="<b>Цена</b>: %{y:.2f} ₽<br>" +
                      "<b>Дата</b>: %{x}<br>" +
                      "<extra></extra>"
    ))

    # Добавляем область между high и low для наглядности
    if highs and lows:
        fig.add_trace(go.Scatter(
            x=dates + dates[::-1],
            y=highs + lows[::-1],
            fill="toself",
            fillcolor="rgba(50, 120, 200, 0.1)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Диапазон High-Low",
            hoverinfo="skip",
            showlegend=False
        ))

    # Обработка сделок
    if trades:
        entries = []
        exits = []

        for trade in trades:
            try:
                timestamp = trade.get("timestamp")
                if isinstance(timestamp, str):
                    trade_date = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00"))
                else:
                    trade_date = timestamp

                price = safe_float(trade.get("price", {}))
                size = safe_float(trade.get("size", {}))
                side = trade.get("side", "")

                trade_info = {
                    "date": trade_date,
                    "price": price,
                    "size": size,
                    "side": side
                }

                # Определяем тип сделки
                if side in ["SIDE_BUY", "1", "BUY"]:
                    entries.append(trade_info)
                elif side in ["SIDE_SELL", "2", "SELL"]:
                    exits.append(trade_info)

            except (ValueError, TypeError, KeyError):
                continue

        # Точки входа (покупки)
        if entries:
            fig.add_trace(go.Scatter(
                x=[t["date"] for t in entries],
                y=[t["price"] for t in entries],
                mode="markers",
                name="Вход (покупка)",
                marker=dict(
                    symbol="triangle-up",
                    size=14,
                    color="rgb(50, 200, 50)",
                    line=dict(color="rgb(30, 150, 30)", width=2)
                ),
                hovertemplate="<b>🔺 ВХОД</b><br>" +
                              "Цена: %{y:.2f} ₽<br>" +
                              "Дата: %{x}<br>" +
                              "<extra></extra>"
            ))

        # Точки выхода (продажи)
        if exits:
            fig.add_trace(go.Scatter(
                x=[t["date"] for t in exits],
                y=[t["price"] for t in exits],
                mode="markers",
                name="Выход (продажа)",
                marker=dict(
                    symbol="triangle-down",
                    size=14,
                    color="rgb(220, 50, 50)",
                    line=dict(color="rgb(180, 30, 30)", width=2)
                ),
                hovertemplate="<b>🔻 ВЫХОД</b><br>" +
                              "Цена: %{y:.2f} ₽<br>" +
                              "Дата: %{x}<br>" +
                              "<extra></extra>"
            ))

    # Настройка внешнего вида
    fig.update_layout(
        title="Сделки на истории котировок",
        xaxis_title="Дата",
        yaxis_title="Цена, ₽",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=30, t=80, b=60)
    )

    # Настройка осей
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)",
        rangeslider_visible=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)"
    )

    return fig.to_json()
