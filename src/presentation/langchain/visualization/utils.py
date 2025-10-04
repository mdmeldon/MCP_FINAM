"""
Вспомогательные функции для визуализации.
"""

from typing import Dict, Any
from decimal import Decimal


# Маппинг тикеров на секторы экономики (упрощенный)
SECTOR_MAPPING = {
    # Технологии
    "YNDX": "Технологии",
    "VKCO": "Технологии",
    "TCSG": "Технологии",
    "OZON": "Технологии",
    "MTSS": "Телекоммуникации",

    # Финансы
    "SBER": "Финансы",
    "VTBR": "Финансы",
    "TRNFP": "Финансы",
    "MOEX": "Финансы",

    # Энергетика
    "GAZP": "Энергетика",
    "LKOH": "Энергетика",
    "ROSN": "Энергетика",
    "TATN": "Энергетика",
    "NVTK": "Энергетика",
    "SNGS": "Энергетика",

    # Металлургия
    "GMKN": "Металлургия",
    "NLMK": "Металлургия",
    "MAGN": "Металлургия",
    "ALRS": "Металлургия",

    # Потребительский сектор
    "MGNT": "Ритейл",
    "FIVE": "Ритейл",
    "FIXP": "Ритейл",

    # Химия и удобрения
    "PHOR": "Химия",

    # Транспорт
    "AFLT": "Транспорт",

    # Электроэнергетика
    "FEES": "Электроэнергетика",
    "HYDR": "Электроэнергетика",
    "IRAO": "Электроэнергетика",
}


def get_sector_by_ticker(symbol: str) -> str:
    """
    Определяет сектор экономики по тикеру инструмента.

    Args:
        symbol: Символ инструмента (например, "SBER@TQBR" или "SBER")

    Returns:
        Название сектора экономики
    """
    # Извлекаем тикер из полного символа (до @)
    ticker = symbol.split("@")[0].upper()

    # Проверяем наличие в маппинге
    return SECTOR_MAPPING.get(ticker, "Прочее")


def calculate_pnl(trade: Dict[str, Any]) -> float:
    """
    Рассчитывает прибыль/убыток по сделке.

    Args:
        trade: Данные сделки с полями price, size, side

    Returns:
        Значение P&L для сделки
    """
    try:
        price = float(trade.get("price", {}).get("value", 0))
        size = float(trade.get("size", {}).get("value", 0))
        side = trade.get("side", "")

        # Для простоты считаем P&L относительно предыдущей сделки
        # В реальности нужно учитывать открытие/закрытие позиций
        if side == "SIDE_SELL" or side == "2":
            return price * size
        else:
            return -price * size

    except (ValueError, KeyError, TypeError):
        return 0.0


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасное преобразование значения в float.

    Args:
        value: Значение для преобразования (может быть dict с 'value', str, int, float)
        default: Значение по умолчанию при ошибке

    Returns:
        Преобразованное значение или default
    """
    try:
        if isinstance(value, dict):
            value = value.get("value", default)

        if isinstance(value, str):
            # Убираем пробелы и запятые
            value = value.replace(" ", "").replace(",", ".")

        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default


def format_currency(value: float, currency: str = "₽") -> str:
    """
    Форматирует денежное значение.

    Args:
        value: Числовое значение
        currency: Символ валюты

    Returns:
        Отформатированная строка
    """
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f} млн {currency}"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.2f} тыс {currency}"
    else:
        return f"{value:.2f} {currency}"
