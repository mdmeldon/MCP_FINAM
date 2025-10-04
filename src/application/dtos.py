import datetime
from enum import Enum, auto
from typing import Any

from pydantic import BaseModel, Field


class FinamApiErrorMessageDTO(BaseModel):
    code: int
    message: str
    details: list[Any]


class AuthRespDTO(BaseModel):
    token: str


class TokenDetailsDTO(BaseModel):
    created_at: datetime.datetime
    expires_at: datetime.datetime
    md_permissions: list[Any]
    account_ids: list[Any]
    readonly: bool


class ValueDTO(BaseModel):
    value: str = "0.0"


class PositionDTO(BaseModel):
    symbol: str
    quantity: ValueDTO
    average_price: ValueDTO
    current_price: ValueDTO
    daily_pnl: ValueDTO
    unrealized_pnl: ValueDTO


class CashDTO(BaseModel):
    currency_code: str = "0"
    units: str = "RUB"
    nanos: int = 0


class PortfolioMCDTO(BaseModel):
    available_cash: ValueDTO
    initial_margin: ValueDTO
    maintenance_margin: ValueDTO


class AccountDTO(BaseModel):
    account_id: str
    type: str
    status: str
    equity: ValueDTO
    unrealized_profit: ValueDTO
    positions: list[PositionDTO]
    cash: list[CashDTO]
    portfolio_mc: PortfolioMCDTO


class TradeDTO(BaseModel):
    trade_id: str
    symbol: str
    price: ValueDTO
    size: ValueDTO
    side: str
    timestamp: datetime.datetime
    order_id: str
    account_id: str


class TradesRespDTO(BaseModel):
    trades: list[TradeDTO]


class TransactionDTO(BaseModel):
    id: str
    category: str
    timestamp: datetime.datetime
    symbol: str
    change: CashDTO
    transaction_category: str
    transaction_name: str


class TransactionsRespDTO(BaseModel):
    transactions: list[TransactionDTO]


class AssetDTO(BaseModel):
    board: str
    id: str
    ticker: str
    mic: str
    isin: str
    type: str
    name: str
    lot_size: ValueDTO
    decimals: int
    min_step: str
    quote_currency: str


class AssetsRespDTO(BaseModel):
    assets: list[Any]


class ClockDTO(BaseModel):
    timestamp: datetime.datetime


class ExchangeDTO(BaseModel):
    mic: str
    name: str


class ExchangesRespDTO(BaseModel):
    exchanges: list[ExchangeDTO]


class LongableStatus(str, Enum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    AVAILABLE = "AVAILABLE"
    ACCOUNT_NOT_APPROVED = "ACCOUNT_NOT_APPROVED"


class ShortableStatus(str, Enum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    AVAILABLE = "AVAILABLE"
    HTB = "HTB"
    ACCOUNT_NOT_APPROVED = "ACCOUNT_NOT_APPROVED"
    AVAILABLE_STRATEGY = "AVAILABLE_STRATEGY"


class LongableDTO(BaseModel):
    value: LongableStatus
    halted_days: int


class ShortableDTO(BaseModel):
    value: ShortableStatus
    halted_days: int


class AssetParamsDTO(BaseModel):
    symbol: str
    account_id: str
    tradeable: bool
    longable: LongableDTO
    shortable: ShortableDTO
    long_risk_rate: ValueDTO
    long_collateral: CashDTO
    short_risk_rate: ValueDTO
    long_initial_margin: CashDTO


class DateDTO(BaseModel):
    year: int
    month: int
    day: int


class OptionDTO(BaseModel):
    symbol: str
    type: str
    contract_size: ValueDTO
    trade_last_day: DateDTO
    strike: ValueDTO
    expiration_first_day: DateDTO
    expiration_last_day: DateDTO


class OptionsChainDTO(BaseModel):
    symbol: str
    options: list[OptionDTO]


class IntervalDTO(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime


class SessionDTO(BaseModel):
    type: str
    interval: IntervalDTO


class SymbolScheduleDTO(BaseModel):
    symbol: str
    sessions: list[SessionDTO]


class OrderDetailsDTO(BaseModel):
    account_id: str
    symbol: str
    quantity: ValueDTO
    side: str
    type: str
    time_in_force: str
    limit_price: ValueDTO
    stop_condition: str
    legs: list[Any]
    client_order_id: str
    valid_before: str


class OrderDTO(BaseModel):
    order_id: str
    exec_id: str
    status: str
    order: OrderDetailsDTO
    transact_at: datetime.datetime


class OrderType(str, Enum):
    ORDER_TYPE_UNSPECIFIED = "ORDER_TYPE_UNSPECIFIED"
    ORDER_TYPE_MARKET = "ORDER_TYPE_MARKET"
    ORDER_TYPE_LIMIT = "ORDER_TYPE_LIMIT"
    ORDER_TYPE_STOP = "ORDER_TYPE_STOP"
    ORDER_TYPE_STOP_LIMIT = "ORDER_TYPE_STOP_LIMIT"
    ORDER_TYPE_MULTI_LEG = "ORDER_TYPE_MULTI_LEG"


class Side(Enum):
    SIDE_UNSPECIFIED = 0
    SIDE_BUY = 1
    SIDE_SELL = 2


class StopCondition(Enum):
    STOP_CONDITION_UNSPECIFIED = 0
    STOP_CONDITION_LAST_UP = 1
    STOP_CONDITION_LAST_DOWN = 2


class TimeInForce(Enum):
    TIME_IN_FORCE_UNSPECIFIED = 0
    TIME_IN_FORCE_DAY = 1
    TIME_IN_FORCE_GOOD_TILL_CANCEL = 2
    TIME_IN_FORCE_GOOD_TILL_CROSSING = 3
    TIME_IN_FORCE_EXT = 4
    TIME_IN_FORCE_ON_OPEN = 5
    TIME_IN_FORCE_ON_CLOSE = 6
    TIME_IN_FORCE_IOC = 7
    TIME_IN_FORCE_FOK = 8


class ValidBefore(Enum):
    VALID_BEFORE_UNSPECIFIED = 0
    VALID_BEFORE_END_OF_DAY = 1
    VALID_BEFORE_GOOD_TILL_CANCEL = 2
    VALID_BEFORE_GOOD_TILL_DATE = 3


class LegDTO(BaseModel):
    symbol: str
    quantity: ValueDTO
    side: Side


class GetOrdersDTO(BaseModel):
    orders: list[OrderDTO]


class TimeFrame(str, Enum):
    """
    Доступные таймфреймы для свечей
    """

    TIME_FRAME_UNSPECIFIED = auto()
    TIME_FRAME_M1 = auto()
    TIME_FRAME_M5 = auto()
    TIME_FRAME_M15 = auto()
    TIME_FRAME_M30 = auto()
    TIME_FRAME_H1 = auto()
    TIME_FRAME_H2 = auto()
    TIME_FRAME_H4 = auto()
    TIME_FRAME_H8 = auto()
    TIME_FRAME_D = auto()
    TIME_FRAME_W = auto()
    TIME_FRAME_MN = auto()
    TIME_FRAME_QR = auto()


class BarDTO(BaseModel):
    timestamp: datetime.datetime = Field(description="Метка времени")
    open: ValueDTO = Field(description="Цена открытия свечи")
    high: ValueDTO = Field(description="Максимальная цена свечи")
    low: ValueDTO = Field(description="Минимальная цена свечи")
    close: ValueDTO = Field(description="Цена закрытия свечи")
    volume: ValueDTO = Field(description="Объём торгов за свечу в шт.")


class BarsRespDTO(BaseModel):
    symbol: str = Field(description="Символ инструмента")
    bars: list[BarDTO] = Field(description="Агрегированная свеча")


class LatestTradesDTO(BaseModel):
    symbol: str = Field(description="Символ инструмента")
    trades: list[TradeDTO] = Field(description="Список последних сделок")


class QuoteOption(BaseModel):
    open_interest: ValueDTO
    implied_volatility: ValueDTO
    theoretical_price: ValueDTO
    delta: ValueDTO
    gamma: ValueDTO
    theta: ValueDTO
    vega: ValueDTO
    rho: ValueDTO


class QuoteDTO(BaseModel):
    symbol: str = Field(description="Символ инструмента")
    timestamp: datetime.datetime = Field(description="Метка времени")
    ask: str = Field(description="Аск. 0 при отсутствии активного аска")
    ask_size: str = Field(description="Размер аска")
    bid: str = Field(description="Бид. 0 при отсутствии активного бида")
    bid_size: str = Field(description="Размер бида")
    last: str = Field(description="Цена последней сделки")
    last_size: str = Field(description="Размер последней сделки")
    volume: str = Field(description="Дневной объем сделок")
    turnover: str = Field(description="Дневной оборот сделок")
    open: str = Field(description="Цена открытия.Дневная")
    high: str = Field(description="Максимальная цена.Дневная")
    low: str = Field(description="Минимальная цена.Дневная")
    close: str = Field(description="Цена закрытия.Дневная")
    change: str = Field(description="Изменение цены(last минус close)")
    option: QuoteOption = Field(description="Информация об опционе")


class LastQuoteDTO(BaseModel):
    symbol: str = Field(description="Символ инструмента")
    quote: QuoteDTO = Field(description="Цена последней сделки")


class OrderBookRowAction(str, Enum):
    ACTION_UNSPECIFIED = auto()
    ACTION_REMOVE = auto()
    ACTION_ADD = auto()
    ACTION_UPDATE = auto()


class OrderBookRowDTO(BaseModel):
    price: ValueDTO
    sell_size: ValueDTO
    buy_size: ValueDTO
    action: OrderBookRowAction
    mpid: str
    timestamp: datetime.datetime


class OrderBookDTO(BaseModel):
    rows: list[OrderBookRowDTO]


class OrderBookRespDTO(BaseModel):
    symbol: str = Field(description="Символ инструмента")
    orderbook: OrderBookDTO