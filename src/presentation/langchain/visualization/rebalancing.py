"""
Визуализация симуляции ребалансировки портфеля.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Tuple
from .utils import safe_float, format_currency, get_sector_by_ticker


def calculate_target_weights(
    positions: List[Dict[str, Any]],
    strategy: str = "equal"
) -> Dict[str, float]:
    """
    Рассчитывает целевые веса для портфеля на основе выбранной стратегии.

    Args:
        positions: Список позиций из AccountDTO.positions
        strategy: Стратегия ребалансировки:
                 - "equal": Равновесное распределение (все позиции равны)
                 - "sector_equal": Равновесное распределение по секторам

    Returns:
        Словарь {symbol: target_weight} с целевыми весами
    """
    if not positions:
        return {}

    if strategy == "equal":
        # Равные веса для всех позиций
        num_positions = len(positions)
        target_weight = 1.0 / num_positions if num_positions > 0 else 0
        return {pos["symbol"]: target_weight for pos in positions}

    elif strategy == "sector_equal":
        # Группируем по секторам
        sectors = {}
        for pos in positions:
            symbol = pos.get("symbol", "")
            sector = get_sector_by_ticker(symbol)
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(symbol)

        # Равные веса по секторам, внутри сектора - равномерно
        target_weights = {}
        num_sectors = len(sectors)
        sector_weight = 1.0 / num_sectors if num_sectors > 0 else 0

        for sector, symbols in sectors.items():
            num_symbols = len(symbols)
            symbol_weight = sector_weight / num_symbols if num_symbols > 0 else 0
            for symbol in symbols:
                target_weights[symbol] = symbol_weight

        return target_weights

    return {}


def create_rebalancing_table(
    positions: List[Dict[str, Any]],
    strategy: str = "equal"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Создает интерактивную таблицу с симуляцией ребалансировки портфеля.

    Таблица показывает:
    - Текущие веса инструментов
    - Целевые веса на основе выбранной стратегии
    - Необходимые сделки (покупка/продажа) для достижения баланса
    - Стоимость сделок

    Args:
        positions: Список позиций из AccountDTO.positions
        strategy: Стратегия ребалансировки ("equal" или "sector_equal")

    Returns:
        Tuple: (JSON графика таблицы, список рекомендуемых сделок)

    Example:
        >>> positions = [...]
        >>> fig_json, trades = create_rebalancing_table(positions, "equal")
    """
    if not positions:
        # Пустая таблица
        fig = go.Figure(data=[go.Table(
            header=dict(values=["Сообщение"]),
            cells=dict(values=[["Нет позиций для ребалансировки"]])
        )])
        fig.update_layout(
            title="Симуляция ребалансировки портфеля",
            height=300
        )
        return fig.to_json(), []

    # Рассчитываем текущие веса и стоимости
    data = []
    total_value = 0

    for pos in positions:
        symbol = pos.get("symbol", "UNKNOWN")
        quantity = safe_float(pos.get("quantity", {}))
        current_price = safe_float(pos.get("current_price", {}))
        current_value = quantity * current_price
        total_value += current_value

        data.append({
            "symbol": symbol,
            "ticker": symbol.split("@")[0],
            "sector": get_sector_by_ticker(symbol),
            "quantity": quantity,
            "current_price": current_price,
            "current_value": current_value,
        })

    # Рассчитываем текущие веса
    for item in data:
        item["current_weight"] = (
            item["current_value"] / total_value * 100) if total_value > 0 else 0

    # Рассчитываем целевые веса
    target_weights = calculate_target_weights(positions, strategy)

    # Рассчитываем необходимые изменения
    trades = []
    for item in data:
        symbol = item["symbol"]
        target_weight = target_weights.get(symbol, 0) * 100  # в процентах
        target_value = total_value * (target_weight / 100)
        value_diff = target_value - item["current_value"]
        quantity_diff = value_diff / \
            item["current_price"] if item["current_price"] > 0 else 0

        item["target_weight"] = target_weight
        item["target_value"] = target_value
        item["value_diff"] = value_diff
        item["quantity_diff"] = quantity_diff

        # Формируем рекомендацию по сделке
        if abs(quantity_diff) > 0.01:  # Минимальный порог для сделки
            action = "Купить" if quantity_diff > 0 else "Продать"
            trades.append({
                "symbol": symbol,
                "ticker": item["ticker"],
                "action": action,
                "quantity": abs(quantity_diff),
                "price": item["current_price"],
                "value": abs(value_diff),
                "current_weight": item["current_weight"],
                "target_weight": target_weight
            })

    # Создаем DataFrame для таблицы
    df = pd.DataFrame(data)

    # Создаем таблицу с Plotly
    fig = go.Figure(data=[go.Table(
        columnwidth=[100, 80, 120, 90, 90, 90, 90, 120, 120],
        header=dict(
            values=[
                "<b>Тикер</b>",
                "<b>Сектор</b>",
                "<b>Текущий вес</b>",
                "<b>Целевой вес</b>",
                "<b>Разница</b>",
                "<b>Текущее кол-во</b>",
                "<b>Изменение кол-ва</b>",
                "<b>Текущая стоимость</b>",
                "<b>Действие</b>"
            ],
            fill_color="#1f77b4",
            align="center",
            font=dict(color="white", size=12, family="Arial")
        ),
        cells=dict(
            values=[
                df["ticker"],
                df["sector"],
                [f"{w:.2f}%" for w in df["current_weight"]],
                [f"{w:.2f}%" for w in df["target_weight"]],
                [f"{w:.2f}%" for w in (
                    df["target_weight"] - df["current_weight"])],
                [f"{q:.0f}" for q in df["quantity"]],
                [f"{q:+.0f}" if abs(q) >
                 0.01 else "—" for q in df["quantity_diff"]],
                [format_currency(v) for v in df["current_value"]],
                [
                    f"{'Купить' if qd > 0.01 else 'Продать' if qd < -0.01 else '—'} {abs(qd):.0f} шт."
                    if abs(qd) > 0.01 else "—"
                    for qd in df["quantity_diff"]
                ]
            ],
            fill_color=[
                ["white" if i % 2 == 0 else "#f0f0f0" for i in range(len(df))]
            ],
            align=["left", "left", "center", "center",
                   "center", "right", "right", "right", "left"],
            font=dict(color="black", size=11, family="Arial"),
            height=30
        )
    )])

    # Настройка внешнего вида
    strategy_name = "Равновесное распределение" if strategy == "equal" else "Равновесное по секторам"
    fig.update_layout(
        title={
            "text": f"⚖️ Симуляция ребалансировки портфеля ({strategy_name})",
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=18, color="#1f77b4")
        },
        height=max(400, 150 + len(df) * 35),
        margin=dict(l=20, r=20, t=80, b=20)
    )

    return fig.to_json(), trades


def create_rebalancing_comparison_chart(
    positions: List[Dict[str, Any]],
    strategy: str = "equal"
) -> str:
    """
    Создает столбчатую диаграмму сравнения текущих и целевых весов.

    Args:
        positions: Список позиций из AccountDTO.positions
        strategy: Стратегия ребалансировки

    Returns:
        JSON-строка с графиком Plotly

    Example:
        >>> positions = [...]
        >>> fig_json = create_rebalancing_comparison_chart(positions, "equal")
    """
    if not positions:
        fig = go.Figure()
        fig.add_annotation(
            text="Нет позиций для отображения",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title="Сравнение весов портфеля",
            height=400
        )
        return fig.to_json()

    # Рассчитываем текущие веса
    data = []
    total_value = 0

    for pos in positions:
        symbol = pos.get("symbol", "UNKNOWN")
        quantity = safe_float(pos.get("quantity", {}))
        current_price = safe_float(pos.get("current_price", {}))
        current_value = quantity * current_price
        total_value += current_value

        data.append({
            "symbol": symbol,
            "ticker": symbol.split("@")[0],
            "current_value": current_value,
        })

    # Рассчитываем текущие веса
    for item in data:
        item["current_weight"] = (
            item["current_value"] / total_value * 100) if total_value > 0 else 0

    # Рассчитываем целевые веса
    target_weights = calculate_target_weights(positions, strategy)

    for item in data:
        symbol = item["symbol"]
        item["target_weight"] = target_weights.get(symbol, 0) * 100

    # Создаем DataFrame
    df = pd.DataFrame(data).sort_values("current_weight", ascending=True)

    # Создаем grouped bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Текущий вес",
        x=df["current_weight"],
        y=df["ticker"],
        orientation="h",
        marker=dict(color="rgb(220, 100, 50)"),
        hovertemplate="<b>%{y}</b><br>Текущий вес: %{x:.2f}%<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name="Целевой вес",
        x=df["target_weight"],
        y=df["ticker"],
        orientation="h",
        marker=dict(color="rgb(50, 180, 220)"),
        hovertemplate="<b>%{y}</b><br>Целевой вес: %{x:.2f}%<extra></extra>"
    ))

    # Настройка внешнего вида
    fig.update_layout(
        title={
            "text": "📊 Сравнение текущих и целевых весов инструментов",
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=16, color="#1f77b4")
        },
        xaxis_title="Вес в портфеле, %",
        yaxis_title="Инструмент",
        barmode="group",
        template="plotly_white",
        height=max(400, 150 + len(df) * 25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=80, r=30, t=80, b=60)
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(200, 200, 200, 0.3)"
    )

    return fig.to_json()
