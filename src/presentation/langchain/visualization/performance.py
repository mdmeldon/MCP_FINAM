"""
Визуализация кривой доходности и расчет метрик стратегии.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .utils import safe_float, format_currency


def calculate_metrics(trades: List[Dict[str, Any]], initial_capital: float) -> Dict[str, Any]:
    """
    Рассчитывает ключевые метрики торговой стратегии.

    Args:
        trades: Список сделок
        initial_capital: Начальный капитал

    Returns:
        Словарь с метриками (профит, просадка, винрейт и т.д.)
    """
    if not trades:
        return {
            "Итоговый капитал": format_currency(initial_capital),
            "Общая прибыль": format_currency(0),
            "Доходность": "0.00%",
            "Макс. просадка": "0.00%",
            "Всего сделок": 0,
            "Прибыльных": 0,
            "Убыточных": 0,
            "Винрейт": "0.0%",
        }

    # Создаем DataFrame для анализа
    df_trades = []
    position_size = 0
    position_avg_price = 0
    total_pnl = 0

    profitable_trades = 0
    losing_trades = 0

    for trade in trades:
        price = safe_float(trade.get("price", {}))
        size = safe_float(trade.get("size", {}))
        side = trade.get("side", "")
        timestamp = trade.get("timestamp")

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()

        trade_pnl = 0

        # Упрощенный расчет P&L для пары сделок вход-выход
        if side in ["SIDE_BUY", "1", "BUY"]:
            # Покупка - открытие/увеличение позиции
            if position_size == 0:
                position_avg_price = price
            else:
                # Усреднение
                position_avg_price = (
                    position_avg_price * position_size + price * size) / (position_size + size)
            position_size += size
        elif side in ["SIDE_SELL", "2", "SELL"]:
            # Продажа - закрытие/уменьшение позиции
            if position_size > 0:
                trade_pnl = (price - position_avg_price) * \
                    min(size, position_size)
                total_pnl += trade_pnl
                position_size -= min(size, position_size)

                if trade_pnl > 0:
                    profitable_trades += 1
                elif trade_pnl < 0:
                    losing_trades += 1

        df_trades.append({
            "timestamp": timestamp,
            "price": price,
            "size": size,
            "side": side,
            "pnl": trade_pnl,
            "cumulative_pnl": total_pnl,
            "capital": initial_capital + total_pnl
        })

    df = pd.DataFrame(df_trades)

    if len(df) == 0:
        return {
            "Итоговый капитал": format_currency(initial_capital),
            "Общая прибыль": format_currency(0),
            "Доходность": "0.00%",
            "Макс. просадка": "0.00%",
            "Всего сделок": 0,
            "Прибыльных": 0,
            "Убыточных": 0,
            "Винрейт": "0.0%",
        }

    # Рассчитываем метрики
    final_capital = df["capital"].iloc[-1]
    total_return = ((final_capital - initial_capital) / initial_capital) * 100

    # Максимальная просадка
    df["peak"] = df["capital"].cummax()
    df["drawdown"] = ((df["capital"] - df["peak"]) / df["peak"]) * 100
    max_drawdown = df["drawdown"].min()

    # Количество сделок
    total_trades = len(trades)
    closed_positions = profitable_trades + losing_trades

    winrate = (profitable_trades / closed_positions *
               100) if closed_positions > 0 else 0

    return {
        "Итоговый капитал": format_currency(final_capital),
        "Общая прибыль": format_currency(total_pnl),
        "Доходность": f"{total_return:.2f}%",
        "Макс. просадка": f"{max_drawdown:.2f}%",
        "Всего сделок": total_trades,
        "Прибыльных": profitable_trades,
        "Убыточных": losing_trades,
        "Винрейт": f"{winrate:.1f}%",
    }


def create_performance_chart(
    trades: List[Dict[str, Any]],
    initial_capital: float = 100000
) -> Tuple[str, Dict[str, Any]]:
    """
    Создает график кривой доходности с двумя подграфиками:
    1. Кривая роста капитала
    2. График просадки

    Также рассчитывает ключевые метрики стратегии.

    Args:
        trades: Список сделок с информацией о price, size, side, timestamp
        initial_capital: Начальный капитал (по умолчанию 100,000)

    Returns:
        Tuple: (JSON графика, словарь метрик)

    Example:
        >>> trades = [...]
        >>> fig_json, metrics = create_performance_chart(trades, 100000)
    """
    # Рассчитываем метрики
    metrics = calculate_metrics(trades, initial_capital)

    # Если нет сделок, возвращаем пустой график
    if not trades:
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Кривая роста капитала", "Просадка"),
            vertical_spacing=0.1
        )

        fig.add_annotation(
            text="Нет данных о сделках для анализа",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
            row=1,
            col=1
        )

        fig.update_layout(
            title="Анализ доходности стратегии",
            height=600
        )

        return fig.to_json(), metrics

    # Создаем DataFrame для визуализации
    df_trades = []
    position_size = 0
    position_avg_price = 0
    total_pnl = 0

    for trade in trades:
        price = safe_float(trade.get("price", {}))
        size = safe_float(trade.get("size", {}))
        side = trade.get("side", "")
        timestamp = trade.get("timestamp")

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()

        trade_pnl = 0

        if side in ["SIDE_BUY", "1", "BUY"]:
            if position_size == 0:
                position_avg_price = price
            else:
                position_avg_price = (
                    position_avg_price * position_size + price * size) / (position_size + size)
            position_size += size
        elif side in ["SIDE_SELL", "2", "SELL"]:
            if position_size > 0:
                trade_pnl = (price - position_avg_price) * \
                    min(size, position_size)
                total_pnl += trade_pnl
                position_size -= min(size, position_size)

        df_trades.append({
            "timestamp": timestamp,
            "pnl": trade_pnl,
            "cumulative_pnl": total_pnl,
            "capital": initial_capital + total_pnl
        })

    df = pd.DataFrame(df_trades)

    # Рассчитываем просадку
    df["peak"] = df["capital"].cummax()
    df["drawdown"] = ((df["capital"] - df["peak"]) / df["peak"]) * 100

    # Создаем график с двумя подграфиками
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Кривая роста капитала", "Просадка портфеля"),
        vertical_spacing=0.1,
        shared_xaxes=True
    )

    # График 1: Кривая капитала
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["capital"],
            mode="lines",
            name="Капитал",
            line=dict(color="rgb(50, 180, 50)", width=2.5),
            fill="tonexty",
            fillcolor="rgba(50, 180, 50, 0.1)",
            hovertemplate="<b>Капитал</b>: %{y:,.0f} ₽<br>" +
                          "<b>Дата</b>: %{x}<br>" +
                          "<extra></extra>"
        ),
        row=1,
        col=1
    )

    # Добавляем линию начального капитала
    fig.add_hline(
        y=initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Начальный капитал: {format_currency(initial_capital)}",
        annotation_position="right",
        row=1,
        col=1
    )

    # График 2: Просадка
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["drawdown"],
            mode="lines",
            name="Просадка",
            line=dict(color="rgb(220, 50, 50)", width=2),
            fill="tozeroy",
            fillcolor="rgba(220, 50, 50, 0.3)",
            hovertemplate="<b>Просадка</b>: %{y:.2f}%<br>" +
                          "<b>Дата</b>: %{x}<br>" +
                          "<extra></extra>"
        ),
        row=2,
        col=1
    )

    # Настройка внешнего вида
    fig.update_layout(
        title={
            "text": "Анализ доходности торговой стратегии",
            "x": 0.5,
            "xanchor": "center"
        },
        hovermode="x unified",
        template="plotly_white",
        height=700,
        showlegend=False,
        margin=dict(l=70, r=30, t=100, b=60)
    )

    # Настройка осей
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)",
        row=2,
        col=1
    )

    fig.update_yaxes(
        title_text="Капитал, ₽",
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)",
        row=1,
        col=1
    )

    fig.update_yaxes(
        title_text="Просадка, %",
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)",
        row=2,
        col=1
    )

    return fig.to_json(), metrics


def create_portfolio_performance_chart(
    portfolio_data: List[Dict[str, Any]],
    benchmark_data: List[Dict[str, Any]],
    portfolio_name: str = "Портфель",
    benchmark_name: str = "Бенчмарк (IMOEX)"
) -> str:
    """
    Создает график сравнения исторической доходности портфеля с бенчмарком.

    График нормализует цены к начальному значению (100%) и показывает
    относительное изменение стоимости портфеля и бенчмарка во времени.

    Args:
        portfolio_data: Список исторических данных портфеля с полями:
                       - timestamp: дата/время
                       - value: стоимость портфеля
        benchmark_data: Список баров бенчмарка (результат bars из MCP) с полями:
                       - timestamp: дата/время
                       - close: цена закрытия
        portfolio_name: Название портфеля для легенды
        benchmark_name: Название бенчмарка для легенды

    Returns:
        JSON-строка с графиком Plotly

    Example:
        >>> portfolio = [{"timestamp": "2024-01-01", "value": 100000}, ...]
        >>> benchmark = [{"timestamp": "2024-01-01", "close": {"value": "3500"}}, ...]
        >>> fig_json = create_portfolio_performance_chart(portfolio, benchmark)
    """
    if not portfolio_data and not benchmark_data:
        # Пустой график с сообщением
        fig = go.Figure()
        fig.add_annotation(
            text="Нет данных для отображения",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title="График исторической доходности",
            height=500
        )
        return fig.to_json()

    # Создаем DataFrame для портфеля
    portfolio_df = None
    if portfolio_data:
        portfolio_records = []
        for item in portfolio_data:
            timestamp = item.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00"))
                except:
                    continue

            value = safe_float(item.get("value", {}))
            if value > 0:
                portfolio_records.append({
                    "timestamp": timestamp,
                    "value": value
                })

        if portfolio_records:
            portfolio_df = pd.DataFrame(
                portfolio_records).sort_values("timestamp")
            # Нормализуем к начальному значению
            initial_value = portfolio_df["value"].iloc[0]
            portfolio_df["normalized"] = (
                portfolio_df["value"] / initial_value - 1) * 100

    # Создаем DataFrame для бенчмарка
    benchmark_df = None
    if benchmark_data:
        benchmark_records = []
        for bar in benchmark_data:
            timestamp = bar.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00"))
                except:
                    continue

            close_price = safe_float(bar.get("close", {}))
            if close_price > 0:
                benchmark_records.append({
                    "timestamp": timestamp,
                    "close": close_price
                })

        if benchmark_records:
            benchmark_df = pd.DataFrame(
                benchmark_records).sort_values("timestamp")
            # Нормализуем к начальному значению
            initial_close = benchmark_df["close"].iloc[0]
            benchmark_df["normalized"] = (
                benchmark_df["close"] / initial_close - 1) * 100

    # Создаем график
    fig = go.Figure()

    # Добавляем линию портфеля
    if portfolio_df is not None:
        fig.add_trace(go.Scatter(
            x=portfolio_df["timestamp"],
            y=portfolio_df["normalized"],
            mode="lines",
            name=portfolio_name,
            line=dict(color="rgb(50, 180, 220)", width=3),
            hovertemplate="<b>" + portfolio_name + "</b><br>" +
                          "Доходность: %{y:.2f}%<br>" +
                          "Дата: %{x}<br>" +
                          "<extra></extra>"
        ))

    # Добавляем линию бенчмарка
    if benchmark_df is not None:
        fig.add_trace(go.Scatter(
            x=benchmark_df["timestamp"],
            y=benchmark_df["normalized"],
            mode="lines",
            name=benchmark_name,
            line=dict(color="rgb(220, 100, 50)", width=2, dash="dash"),
            hovertemplate="<b>" + benchmark_name + "</b><br>" +
                          "Доходность: %{y:.2f}%<br>" +
                          "Дата: %{x}<br>" +
                          "<extra></extra>"
        ))

    # Добавляем нулевую линию
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="gray",
        annotation_text="Начальное значение",
        annotation_position="left"
    )

    # Настройка внешнего вида
    fig.update_layout(
        title={
            "text": "📈 График исторической доходности портфеля vs Бенчмарк",
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=18, color="#1f77b4")
        },
        xaxis_title="Дата",
        yaxis_title="Доходность, %",
        hovermode="x unified",
        template="plotly_white",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        margin=dict(l=60, r=30, t=100, b=60)
    )

    # Настройка сетки
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)"
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)",
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="rgba(150, 150, 150, 0.5)"
    )

    return fig.to_json()
