"""
LangChain инструменты для создания визуализаций.

Эти инструменты позволяют агенту создавать интерактивные графики
на основе данных, полученных из Finam API.
"""

import json
import streamlit as st
from langchain.tools import tool
from typing import Optional
from src.presentation.langchain.visualization import (
    create_portfolio_sunburst,
    create_trades_chart,
    create_performance_chart,
)


@tool
def visualize_portfolio(account_data: str) -> str:
    """
    Создает интерактивную Sunburst диаграмму структуры портфеля по секторам экономики.

    Используй этот инструмент после получения данных об аккаунте через get_account.
    Диаграмма показывает распределение активов по секторам и отдельным инструментам,
    размер сегмента соответствует стоимости позиции, цвет - доходности.

    Args:
        account_data: JSON-строка с данными аккаунта (результат get_account из MCP).
                     Должен содержать поле "positions" со списком позиций.

    Returns:
        Описание созданной визуализации и краткую статистику

    Example:
        >>> # После получения данных аккаунта:
        >>> account_json = '{"positions": [...], "equity": {...}}'
        >>> result = visualize_portfolio(account_json)
    """
    try:
        # Парсим данные
        data = json.loads(account_data)
        positions = data.get("positions", [])

        if not positions:
            return "❌ В портфеле нет активных позиций для визуализации."

        # Создаем визуализацию
        fig_json = create_portfolio_sunburst(positions)

        # Сохраняем в session_state для отображения
        if "visualizations" not in st.session_state:
            st.session_state["visualizations"] = []

        st.session_state["visualizations"].append({
            "type": "sunburst",
            "data": fig_json,
            "title": "📊 Структура портфеля по секторам экономики"
        })

        # Формируем краткую статистику
        total_positions = len(positions)
        sectors = set()
        total_value = 0

        for pos in positions:
            symbol = pos.get("symbol", "")
            from src.presentation.langchain.visualization.utils import get_sector_by_ticker, safe_float
            sector = get_sector_by_ticker(symbol)
            sectors.add(sector)

            quantity = safe_float(pos.get("quantity", {}))
            current_price = safe_float(pos.get("current_price", {}))
            total_value += quantity * current_price

        return f"""✅ Создана интерактивная Sunburst диаграмма распределения портфеля!

📈 Краткая статистика:
- Всего позиций: {total_positions}
- Секторов экономики: {len(sectors)}
- Общая стоимость: {total_value:,.0f} ₽

💡 Диаграмма отображена выше. Кликни на сектор для детального просмотра инструментов.
Наведи курсор на сегмент для просмотра подробной информации."""

    except json.JSONDecodeError:
        return "❌ Ошибка: Неверный формат JSON данных аккаунта."
    except Exception as e:
        return f"❌ Ошибка при создании визуализации портфеля: {str(e)}"


@tool
def visualize_strategy_backtest(
    bars_data: str,
    trades_data: str,
    initial_capital: Optional[float] = 100000.0
) -> str:
    """
    Создает визуализации для бэктеста торговой стратегии:
    1. График котировок с отмеченными точками входа/выхода
    2. Кривую доходности с метриками (прибыль, просадка, винрейт)

    Используй этот инструмент после получения исторических баров (bars) и 
    симуляции сделок стратегии.

    Args:
        bars_data: JSON-строка с историческими барами (результат bars из MCP).
                   Должен содержать поле "bars" со списком свечей.
        trades_data: JSON-строка со списком сделок стратегии.
                     Каждая сделка должна содержать: timestamp, price, size, side.
        initial_capital: Начальный капитал для расчета доходности (по умолчанию 100,000)

    Returns:
        Описание визуализаций и ключевые метрики стратегии

    Example:
        >>> bars_json = '{"bars": [...]}'
        >>> trades_json = '[{"timestamp": "...", "price": {...}, "side": "SIDE_BUY"}]'
        >>> result = visualize_strategy_backtest(bars_json, trades_json, 100000)
    """
    try:
        # Парсим данные
        bars = json.loads(bars_data)
        trades = json.loads(trades_data)

        # Извлекаем список баров
        bars_list = bars.get("bars", []) if isinstance(bars, dict) else bars
        trades_list = trades if isinstance(trades, list) else [trades]

        if not bars_list:
            return "❌ Нет исторических данных (баров) для визуализации."

        if not trades_list:
            return "⚠️ Нет сделок для визуализации. Создан только график котировок."

        # Создаем визуализации
        trades_fig = create_trades_chart(bars_list, trades_list)
        perf_fig, metrics = create_performance_chart(
            trades_list, initial_capital)

        # Сохраняем в session_state
        if "visualizations" not in st.session_state:
            st.session_state["visualizations"] = []

        st.session_state["visualizations"].extend([
            {
                "type": "trades",
                "data": trades_fig,
                "title": "📈 График сделок на истории котировок"
            },
            {
                "type": "performance",
                "data": perf_fig,
                "title": "💰 Кривая доходности стратегии"
            }
        ])

        # Формируем ответ с метриками
        metrics_text = "\n".join(
            [f"  • **{k}**: {v}" for k, v in metrics.items()])

        return f"""✅ Созданы визуализации бэктеста торговой стратегии!

**📈 График сделок на истории:**
- Отображены исторические цены инструмента
- Точки входа отмечены зелеными треугольниками вверх 🔺
- Точки выхода отмечены красными треугольниками вниз 🔻
- Интерактивные подсказки при наведении

**💰 Кривая доходности и метрики:**
{metrics_text}

💡 Графики отображены выше. Используй интерактивные функции для детального анализа."""

    except json.JSONDecodeError as e:
        return f"❌ Ошибка парсинга JSON: {str(e)}"
    except Exception as e:
        return f"❌ Ошибка при создании визуализации бэктеста: {str(e)}"


@tool
def create_comparison_chart(instruments_data: str) -> str:
    """
    Создает сравнительный график динамики нескольких инструментов.

    Используй этот инструмент для визуального сравнения котировок
    разных инструментов за один период.

    Args:
        instruments_data: JSON-строка со списком инструментов и их историческими данными.
                         Формат: [{"symbol": "...", "bars": [...]}, ...]

    Returns:
        Описание созданной визуализации

    Example:
        >>> data = '[{"symbol": "SBER", "bars": [...]}, {"symbol": "GAZP", "bars": [...]}]'
        >>> result = create_comparison_chart(data)
    """
    try:
        import plotly.graph_objects as go
        from datetime import datetime
        from src.presentation.langchain.visualization.utils import safe_float

        # Парсим данные
        instruments = json.loads(instruments_data)

        if not instruments or not isinstance(instruments, list):
            return "❌ Неверный формат данных. Ожидается список инструментов."

        # Создаем график
        fig = go.Figure()

        for instrument in instruments:
            symbol = instrument.get("symbol", "Unknown")
            bars = instrument.get("bars", [])

            if not bars:
                continue

            # Извлекаем данные
            dates = []
            closes = []

            for bar in bars:
                try:
                    timestamp = bar.get("timestamp")
                    if isinstance(timestamp, str):
                        dates.append(datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")))
                    else:
                        dates.append(timestamp)

                    closes.append(safe_float(bar.get("close", {})))
                except:
                    continue

            # Нормализуем цены к процентам от начальной
            if closes and closes[0] != 0:
                normalized = [(c / closes[0] - 1) * 100 for c in closes]

                fig.add_trace(go.Scatter(
                    x=dates,
                    y=normalized,
                    mode="lines",
                    name=symbol.split("@")[0],
                    hovertemplate=f"<b>{symbol}</b><br>" +
                    "Изменение: %{y:.2f}%<br>" +
                    "Дата: %{x}<br>" +
                    "<extra></extra>"
                ))

        # Настройка внешнего вида
        fig.update_layout(
            title="Сравнение динамики инструментов (нормализовано)",
            xaxis_title="Дата",
            yaxis_title="Изменение, %",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        # Сохраняем визуализацию
        if "visualizations" not in st.session_state:
            st.session_state["visualizations"] = []

        st.session_state["visualizations"].append({
            "type": "comparison",
            "data": fig.to_json(),
            "title": "📊 Сравнительная динамика инструментов"
        })

        instruments_count = len([i for i in instruments if i.get("bars")])

        return f"""✅ Создан сравнительный график динамики инструментов!

📊 Сравнивается {instruments_count} инструмент(ов).
Все цены нормализованы к начальному значению для удобства сравнения.

💡 График отображен выше. Используй легенду для выбора инструментов."""

    except json.JSONDecodeError as e:
        return f"❌ Ошибка парсинга JSON: {str(e)}"
    except Exception as e:
        return f"❌ Ошибка при создании сравнительного графика: {str(e)}"
