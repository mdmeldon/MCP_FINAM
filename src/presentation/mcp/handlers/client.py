"""
Набор MCP-тулов, оборачивающих методы клиента Finam API.

Важная ремарка: передаваемый в инструменты параметр api_token используется
исключительно для получения короткоживущего JWT (≈15 минут), после чего все
запросы выполняются с использованием этого JWT. Клиент автоматически обновляет
JWT при ошибке 401 или около истечения срока.
"""

import datetime
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import aiohttp

from src.application.dtos import (
    Side,
    OrderType,
    TimeInForce,
    StopCondition,
    ValidBefore,
    LegDTO,
    ValueDTO,
    TimeFrame,
    AuthRespDTO,
    TokenDetailsDTO,
    AccountDTO,
    TradesRespDTO,
    TransactionsRespDTO,
    AssetsRespDTO,
    ClockDTO,
    ExchangesRespDTO,
    AssetDTO,
    AssetParamsDTO,
    OptionsChainDTO,
    SymbolScheduleDTO,
    OrderDTO,
    GetOrdersDTO,
    BarsRespDTO,
    LastQuoteDTO,
    LatestTradesDTO,
    OrderBookRespDTO,
)
from src.infrastructure.core.client import Client


def _parse_dt(value: str) -> datetime.datetime:
    dt = datetime.datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _parse_enum(enum_cls, value: Any):
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        # Пробуем по имени (e.g. "SIDE_BUY")
        try:
            return enum_cls[value]
        except Exception:
            pass
    # Пробуем по значению
    return enum_cls(value)


def _parse_leg(leg: Dict[str, Any]) -> LegDTO:
    return LegDTO(
        symbol=str(leg["symbol"]),
        quantity=ValueDTO(value=str(leg.get("quantity", "0"))),
        side=_parse_enum(Side, leg.get("side", "SIDE_UNSPECIFIED")),
    )


@asynccontextmanager
async def _build_client(api_token: str):
    session = aiohttp.ClientSession(base_url="https://api.finam.ru/")
    try:
        yield Client(token=api_token, session=session)
    finally:
        await session.close()


#
# Auth & tokens
#

async def finam_auth(api_token: str) -> AuthRespDTO:
    """Получить JWT по API-токену."""
    async with _build_client(api_token) as client:
        token = await client.auth()
        return token


async def finam_token_details(jwt_token: str) -> TokenDetailsDTO:
    """Получить сведения о JWT (включая expires_at)."""
    async with _build_client("dummy") as client:
        details = await client.token_details(jwt_token)
        return details


#
# Accounts & portfolio
#

async def get_account(api_token: str, account_id: str) -> AccountDTO:
    """Информация по аккаунту."""
    async with _build_client(api_token) as client:
        resp = await client.get_account(account_id)
        return resp


async def trades(api_token: str, account_id: str, start_time: str, end_time: str) -> TradesRespDTO:
    """История сделок за интервал [start_time, end_time] (ISO8601)."""
    async with _build_client(api_token) as client:
        resp = await client.trades(account_id, _parse_dt(start_time), _parse_dt(end_time))
        return resp


async def transactions(api_token: str) -> TransactionsRespDTO:
    """Список транзакций первого доступного аккаунта из токена."""
    async with _build_client(api_token) as client:
        resp = await client.transactions()
        return resp


#
# Reference data
#

async def assets(api_token: str) -> AssetsRespDTO:
    """Список доступных инструментов."""
    async with _build_client(api_token) as client:
        resp = await client.assets()
        return resp


async def clock(api_token: str) -> ClockDTO:
    """Время сервера."""
    async with _build_client(api_token) as client:
        resp = await client.clock()
        return resp


async def exchanges(api_token: str) -> ExchangesRespDTO:
    """Список бирж."""
    async with _build_client(api_token) as client:
        resp = await client.exchanges()
        return resp


async def get_asset(api_token: str, account_id: str, symbol: str) -> AssetDTO:
    """Информация по инструменту symbol."""
    async with _build_client(api_token) as client:
        resp = await client.get_asset(account_id, symbol)
        return resp


async def get_asset_params(api_token: str, account_id: str, symbol: str) -> AssetParamsDTO:
    """Торговые параметры инструмента symbol."""
    async with _build_client(api_token) as client:
        resp = await client.get_asset_params(account_id, symbol)
        return resp


async def options_chain(api_token: str, underlying_symbol: str) -> OptionsChainDTO:
    """Цепочка опционов по базовому активу."""
    async with _build_client(api_token) as client:
        resp = await client.options_chain(underlying_symbol)
        return resp


async def schedule(api_token: str, symbol: str) -> SymbolScheduleDTO:
    """Расписание торгов по инструменту."""
    async with _build_client(api_token) as client:
        resp = await client.schedule(symbol)
        return resp


#
# Orders
#

async def cancel_order(api_token: str, account_id: str, order_id: str) -> OrderDTO:
    """Отменить заявку."""
    async with _build_client(api_token) as client:
        resp = await client.cancel_order(account_id, order_id)
        return resp


async def get_order(api_token: str, account_id: str, order_id: str) -> OrderDTO:
    """Получить заявку по id."""
    async with _build_client(api_token) as client:
        resp = await client.get_order(account_id, order_id)
        return resp


async def get_orders(api_token: str, account_id: str) -> GetOrdersDTO:
    """Список заявок аккаунта."""
    async with _build_client(api_token) as client:
        resp = await client.get_orders(account_id)
        return resp


async def place_order(
    api_token: str,
    account_id: str,
    symbol: str,
    quantity: str,
    side: str,
    type: str,
    time_in_force: str,
    limit_price: Optional[str] = None,
    stop_price: Optional[str] = None,
    stop_condition: Optional[str] = None,
    legs: Optional[Dict[str, Any]] = None,
    client_order_id: Optional[str] = None,
    valid_before: Optional[str] = None,
    comment: Optional[str] = None,
) -> Dict[str, Any]:
    """Выставить заявку. Строковые enum-параметры принимаются как имена (например, SIDE_BUY)."""
    async with _build_client(api_token) as client:
        leg_dto: Optional[LegDTO] = _parse_leg(legs) if legs else None
        resp = await client.place_order(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            side=_parse_enum(Side, side),
            type=_parse_enum(OrderType, type),
            time_in_force=_parse_enum(TimeInForce, time_in_force),
            limit_price=limit_price or "",
            stop_price=stop_price or "",
            stop_condition=_parse_enum(StopCondition, stop_condition) if stop_condition else StopCondition.STOP_CONDITION_UNSPECIFIED,
            legs=leg_dto,  # type: ignore[arg-type]
            client_order_id=client_order_id or "",
            valid_before=_parse_enum(ValidBefore, valid_before) if valid_before else ValidBefore.VALID_BEFORE_UNSPECIFIED,
            comment=comment or "",
        )
        return resp


#
# Market data
#

async def bars(
    api_token: str,
    symbol: str,
    start_time: str,
    end_time: str,
    timeframe: str,
) -> BarsRespDTO:
    """Исторические бары по инструменту. Даты — ISO8601, timeframe — имя enum TimeFrame."""
    async with _build_client(api_token) as client:
        resp = await client.bars(
            symbol=symbol,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            timeframe=_parse_enum(TimeFrame, timeframe),
        )
        return resp


async def last_quote(api_token: str, symbol: str) -> LastQuoteDTO:
    """Последняя котировка."""
    async with _build_client(api_token) as client:
        resp = await client.last_quote(symbol)
        return resp


async def latest_trades(api_token: str, symbol: str) -> LatestTradesDTO:
    """Последние сделки."""
    async with _build_client(api_token) as client:
        resp = await client.latest_trades(symbol)
        return resp


async def order_book(api_token: str, symbol: str) -> OrderBookRespDTO:
    """Текущий стакан."""
    async with _build_client(api_token) as client:
        resp = await client.order_book(symbol)
        return resp