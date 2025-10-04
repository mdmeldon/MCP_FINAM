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
    "HEADHUNTER": "Технологии",
    "CIAN": "Технологии",
    "AAPL": "Технологии",
    "MSFT": "Технологии",
    "GOOG": "Технологии",
    "AMZN": "Технологии",
    "META": "Технологии",
    "TSLA": "Технологии",
    "NFLX": "Технологии",

    # Телекоммуникации
    "MTSS": "Телекоммуникации",
    "RTKM": "Телекоммуникации",
    "TTLK": "Телекоммуникации",

    # Финансы
    "SBER": "Финансы",
    "VTBR": "Финансы",
    "TRNFP": "Финансы",
    "MOEX": "Финансы",
    "SMLT": "Финансы",
    "CBOM": "Финансы",

    # Энергетика
    "GAZP": "Энергетика",
    "LKOH": "Энергетика",
    "ROSN": "Энергетика",
    "TATN": "Энергетика",
    "NVTK": "Энергетика",
    "SNGS": "Энергетика",
    "SIBN": "Энергетика",

    # Металлургия
    "GMKN": "Металлургия",
    "NLMK": "Металлургия",
    "MAGN": "Металлургия",
    "ALRS": "Металлургия",
    "CHMF": "Металлургия",
    "PLZL": "Металлургия",
    "GLD": "Металлургия",

    # Ритейл
    "MGNT": "Ритейл",
    "FIVE": "Ритейл",
    "FIXP": "Ритейл",
    "DSKY": "Ритейл",
    "WMT": "Ритейл",

    # Химия и удобрения
    "PHOR": "Химия",
    "AKRN": "Химия",

    # Транспорт
    "AFLT": "Транспорт",
    "FLOT": "Транспорт",

    # Электроэнергетика
    "FEES": "Электроэнергетика",
    "HYDR": "Электроэнергетика",
    "IRAO": "Электроэнергетика",
    "UPRO": "Электроэнергетика",
    "LSNG": "Электроэнергетика",

    # Производство
    "RUAL": "Производство",
    "PIKK": "Недвижимость",
    "LSRG": "Недвижимость",

    # Фармацевтика
    "GEMC": "Фармацевтика",
    "AFKS": "Фармацевтика",

    "SPY": "ETF"
}

# Цветовая схема для секторов
SECTOR_COLORS = {
    "Технологии": "#1f77b4",           # Синий
    "Телекоммуникации": "#ff7f0e",     # Оранжевый
    "Финансы": "#2ca02c",              # Зеленый
    "Энергетика": "#d62728",           # Красный
    "Металлургия": "#9467bd",          # Фиолетовый
    "Ритейл": "#8c564b",               # Коричневый
    "Химия": "#e377c2",                # Розовый
    "Транспорт": "#7f7f7f",            # Серый
    "Электроэнергетика": "#bcbd22",    # Желто-зеленый
    "Производство": "#17becf",         # Голубой
    "Недвижимость": "#ff9896",         # Светло-красный
    "Фармацевтика": "#98df8a",         # Светло-зеленый
    "ETF": "#98df8a",                  # Светло-зеленый
    "Прочее": "#c7c7c7",               # Светло-серый
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
