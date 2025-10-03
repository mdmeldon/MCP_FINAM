import datetime
from abc import ABC, abstractmethod

from src.application.dtos import AuthRespDTO, TokenDetailsDTO, AccountDTO, TradesRespDTO, TransactionsRespDTO, \
    AssetsRespDTO, ClockDTO, ExchangesRespDTO, AssetDTO, AssetParamsDTO, OptionsChainDTO, SymbolScheduleDTO, \
    OrderDTO, GetOrdersDTO, Side, OrderType, TimeInForce, StopCondition, LegDTO, ValidBefore, TimeFrame, \
    BarsRespDTO, LastQuoteDTO, LatestTradesDTO, OrderBookRespDTO


class IClient(ABC):
    @abstractmethod
    async def auth(self) -> AuthRespDTO:
        """
        [POST] https://api.finam.ru/v1/sessions
        Получение JWT токена из API токена

        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def token_details(self, token: str) -> TokenDetailsDTO:
        """
        [POST] https://api.finam.ru/v1/sessions/details
        Получение информации о токене сессии

        :param token:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def get_account(self, account_id: str) -> AccountDTO:
        """
        [GET] https://api.finam.ru/v1/accounts/{account_id}
        Получение информации по конкретному аккаунту

        :param account_id:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def trades(
        self,
        account_id: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime
    ) -> TradesRespDTO:
        """
        [GET] https://api.finam.ru/v1/accounts/{account_id}/trades
        Получение истории по сделкам аккаунта

        :param account_id:
        :param start_time:
        :param end_time:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def transactions(self) -> TransactionsRespDTO:
        """
        [GET] https://api.finam.ru/v1/accounts/{account_id}/transactions
        Получение списка транзакций аккаунта

        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def assets(self) -> AssetsRespDTO:
        """
        [GET] https://api.finam.ru/v1/assets
        Получение списка доступных инструментов, их описание

        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def clock(self) -> ClockDTO:
        """
        [GET] https://api.finam.ru/v1/assets/clock
        Получение времени на сервере

        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def exchanges(self) -> ExchangesRespDTO:
        """
        [GET] https://api.finam.ru/v1/exchanges
        Получение списка доступных бирж, названия и mic коды

        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def get_asset(self, account_id: str, symbol: str) -> AssetDTO:
        """
        [GET] https://api.finam.ru/v1/assets/{symbol}
        Получение информации по конкретному инструменту

        :param account_id:
        :param symbol:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_asset_params(self, account_id: str, symbol: str) -> AssetParamsDTO:
        """
        [GET] https://api.finam.ru/v1/assets/{symbol}/params
        Получение торговых параметров по инструменту

        :param account_id:
        :param symbol:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def options_chain(self, underlying_symbol: str) -> OptionsChainDTO:
        """
        [GET] https://api.finam.ru/v1/assets/{underlying_symbol}/options
        Получение цепочки опционов для базового актива

        :param underlying_symbol:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def schedule(self, symbol: str) -> SymbolScheduleDTO:
        """
        [GET] https://api.finam.ru/v1/assets/{symbol}/schedule
        Получение расписания торгов для инструмента

        :param symbol:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def cancel_order(self, account_id: str, order_id: str) -> OrderDTO:
        """
        [DELETE] https://api.finam.ru/v1/accounts/{account_id}/orders/{order_id}
        Отмена биржевой заявки

        :param account_id:
        :param order_id:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def get_order(self, account_id: str, order_id: str) -> OrderDTO:
        """
        [GET] https://api.finam.ru/v1/accounts/{account_id}/orders/{order_id}
        Получение информации о конкретном ордере

        :param account_id:
        :param order_id:
        :return:
        """

        raise NotImplementedError()

    @abstractmethod
    async def get_orders(self, account_id: str) -> GetOrdersDTO:
        """
        [GET] https://api.finam.ru/v1/accounts/{account_id}/orders
        Получение списка заявок для аккаунта

        :param account_id:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def place_order(
        self,
        account_id: str,
        symbol: str,
        quantity: str,
        side: Side,
        type: OrderType,
        time_in_force: TimeInForce,
        limit_price: str,
        stop_price: str,
        stop_condition: StopCondition,
        legs: LegDTO,
        client_order_id: str,
        valid_before: ValidBefore,
        comment: str
    ) -> OrderDTO:
        """
        [POST] https://api.finam.ru/v1/accounts/{account_id}/orders
        Выставление биржевой заявки

        :param account_id:      Идентификатор аккаунта
        :param symbol:          Символ инструмента
        :param quantity:        Количество в шт.
        :param side:            Сторона (long или short)
        :param type:            Тип заявки
        :param time_in_force:   Срок действия заявки
        :param limit_price:     Необходимо для лимитной и стоп лимитной заявки
        :param stop_price:      Необходимо для стоп рыночной и стоп лимитной заявки
        :param stop_condition:  Необходимо для стоп рыночной и стоп лимитной заявки
        :param legs:            Необходимо для мульти лег заявки
        :param client_order_id: Уникальный идентификатор заявки. Автоматически генерируется, если не отправлен. (максимум 20 символов)
        :param valid_before:    Срок действия условной заявки. Заполняется для заявок с типом ORDER_TYPE_STOP, ORDER_TYPE_STOP_LIMIT
        :param comment:         Метка заявки. (максимум 128 символов)
        :return: OrderDTO
        """
        raise NotImplementedError()

    @abstractmethod
    async def bars(
        self,
        symbol: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        timeframe: TimeFrame
    ) -> BarsRespDTO:
        """
        [GET] https://api.finam.ru/v1/instruments/{symbol}/bars
        Получение исторических данных по инструменту (агрегированные свечи)

        :param symbol:      Символ инструмента
        :param start_time:  Необходимый таймфрейм
        :param end_time:    Начало запрашиваемого периода
        :param timeframe:   Окончание запрашиваемого периода
        :return: BarsRespDTO
        """
        raise NotImplementedError()

    @abstractmethod
    async def last_quote(
        self,
        symbol: str
    ) -> LastQuoteDTO:
        """
        [GET] https://api.finam.ru/v1/instruments/{symbol}/quotes/latest
        Получение последней котировки по инструменту

        :param symbol:  Символ инструмента
        :return: LastQuoteDTO
        """
        raise NotImplementedError()

    @abstractmethod
    async def latest_trades(
        self,
        symbol: str
    ) -> LatestTradesDTO:
        """
        [GET] https://api.finam.ru/v1/instruments/{symbol}/trades/latest
        Получение списка последних сделок по инструменту

        :param symbol:  Символ инструмента
        :return: LatestTradesDTO
        """
        raise NotImplementedError()

    @abstractmethod
    async def order_book(
        self,
        symbol: str
    ) -> OrderBookRespDTO:
        """
        [GET] https://api.finam.ru/v1/instruments/{symbol}/orderbook
        Получение текущего стакана по инструменту

        :param symbol:  Символ инструмента
        :return: OrderBookRespDTO
        """
        raise NotImplementedError()