import datetime
from collections.abc import Mapping
from typing import Literal, Any

import aiohttp

from src.application.dtos import OrderBookRespDTO, LatestTradesDTO, LastQuoteDTO, TimeFrame, BarsRespDTO, Side, \
    OrderType, TimeInForce, StopCondition, LegDTO, ValidBefore, OrderDTO, GetOrdersDTO, SymbolScheduleDTO, \
    OptionsChainDTO, AssetParamsDTO, AssetDTO, ExchangesRespDTO, ClockDTO, AssetsRespDTO, TransactionsRespDTO, \
    TradesRespDTO, AccountDTO, TokenDetailsDTO, AuthRespDTO
from src.application.interfaces.client import IClient


class Client(IClient):
    """
    Клиент для работы с Finam API.

    Важно: API-токен, передаваемый в конструктор, используется только для
    получения короткоживущего JWT-токена (валиден ~15 минут). Все последующие
    запросы выполняются с использованием этого JWT. Клиент автоматически
    обновляет JWT при получении 401 или при близком истечении его срока.
    """

    def __init__(
        self,
        token: str,
        session: aiohttp.ClientSession | None = None,
        base_url: str = "https://api.finam.ru/",
    ):
        self._base_url = base_url
        if session:
            self.session = session
        else:
            # В aiohttp >=3.8 можно использовать base_url, что мы и делаем
            self.session = aiohttp.ClientSession(base_url=base_url)

        # API-токен, который используется только для /sessions
        self._api_token = token

        # Текущий JWT и его срок жизни
        self._jwt_token: str | None = None
        self._jwt_expires_at: datetime.datetime | None = None

        # Кеш идентификаторов аккаунтов из token_details (может пригодиться)
        self._account_ids: list[str] = []

        self.headers: dict[str, str] = {}

    async def _ensure_jwt(self) -> None:
        """Убедиться, что валидный JWT присутствует. При необходимости — обновить."""
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        # Обновляем, если токена нет или он скоро истечёт (зазор 60 секунд)
        if (
            self._jwt_token is None or
            self._jwt_expires_at is None or
            (self._jwt_expires_at - now).total_seconds() <= 60
        ):
            await self.auth()

    async def _request(
        self,
        method: Literal["GET", "POST", "DELETE"],
        url: str,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        use_auth: bool = True,
    ) -> Any:
        # Для защищённых эндпоинтов гарантируем валидный JWT
        if use_auth:
            await self._ensure_jwt()

        # Добавляем заголовки авторизации для защищённых запросов
        req_headers = self.headers.copy()
        if use_auth and self._jwt_token:
            req_headers["Authorization"] = self._jwt_token

        response = await self.session.request(
            method=method,
            url=url,
            params=self._encode_params(params),
            json=json,
            headers=req_headers if req_headers else None,
        )

        # Если сессия истекла — пробуем обновить JWT и повторить один раз
        if response.status == 401 and use_auth:
            await self.auth()
            response.close()
            response = await self.session.request(
                method=method,
                url=url,
                params=self._encode_params(params),
                json=json,
                headers={"Authorization": self._jwt_token} if self._jwt_token else None,
            )

        # Ошибки HTTP
        if response.status >= 400:
            try:
                payload = await response.json()
            except Exception:
                payload = {"status": response.status, "text": await response.text()}
            # Вызываем стандартную ошибку клиента с подробностями
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=str(payload),
                headers=response.headers,
            )

        # Нормальный ответ — парсим JSON
        return await response.json()

    @staticmethod
    def _encode_params(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if params is None:
            return None
        encoded: dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, datetime.datetime):
                # Используем ISO 8601
                v = value.astimezone(datetime.timezone.utc).isoformat()
            elif hasattr(value, "value"):
                # Для Enum со значением
                v = getattr(value, "value")
            elif hasattr(value, "name"):
                # Для Enum без .value, используем имя
                v = getattr(value, "name")
            else:
                v = value
            encoded[key] = v
        return encoded

    async def auth(self) -> AuthRespDTO:
        # Авторизация выполняется без текущего JWT, только с API-токеном
        payload = {"secret": self._api_token}
        data = await self._request("POST", "/v1/sessions", json=payload, use_auth=False)
        result = AuthRespDTO.model_validate(data)

        # Сохраняем JWT и заголовок
        self._jwt_token = result.token
        self.headers["Authorization"] = self._jwt_token

        # Получаем детали токена, чтобы знать срок действия и список аккаунтов
        try:
            details = await self.token_details(result.token)
            self._jwt_expires_at = details.expires_at
            # account_ids задекларированы как list[Any], приведём к str
            self._account_ids = [str(x) for x in (details.account_ids or [])]
        except Exception:
            # Если /sessions/details недоступен, установим консервативный срок: 14 минут с запасом
            self._jwt_expires_at = (
                datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                + datetime.timedelta(minutes=14)
            )

        return result

    async def token_details(self, token: str) -> TokenDetailsDTO:
        payload = {"token": token}
        data = await self._request("POST", "/v1/sessions/details", json=payload, use_auth=False)
        return TokenDetailsDTO.model_validate(data)

    async def get_account(self, account_id: str) -> AccountDTO:
        data = await self._request("GET", f"/v1/accounts/{account_id}")
        return AccountDTO.model_validate(data)

    async def trades(self, account_id: str, start_time: datetime.datetime,
                     end_time: datetime.datetime) -> TradesRespDTO:
        params = {
            "start_time": start_time,
            "end_time": end_time,
        }
        data = await self._request("GET", f"/v1/accounts/{account_id}/trades", params=params)
        return TradesRespDTO.model_validate(data)

    async def transactions(self) -> TransactionsRespDTO:
        # В интерфейсе не передаётся account_id, используем первый доступный из токена
        if not self._account_ids:
            await self._ensure_jwt()
            # Попробуем получить детали, если ещё не получали
            if not self._account_ids and self._jwt_token:
                try:
                    details = await self.token_details(self._jwt_token)
                    self._account_ids = [str(x) for x in (details.account_ids or [])]
                except Exception:
                    pass
        if not self._account_ids:
            raise ValueError("Не удалось определить account_id для запроса транзакций")
        account_id = self._account_ids[0]
        data = await self._request("GET", f"/v1/accounts/{account_id}/transactions")
        return TransactionsRespDTO.model_validate(data)

    async def assets(self) -> AssetsRespDTO:
        data = await self._request("GET", "/v1/assets")
        return AssetsRespDTO.model_validate(data)

    async def clock(self) -> ClockDTO:
        data = await self._request("GET", "/v1/assets/clock")
        return ClockDTO.model_validate(data)

    async def exchanges(self) -> ExchangesRespDTO:
        data = await self._request("GET", "/v1/exchanges")
        return ExchangesRespDTO.model_validate(data)

    async def get_asset(self, account_id: str, symbol: str) -> AssetDTO:
        # Параметр account_id оставим как query, если API его учитывает
        params = {"account_id": account_id}
        data = await self._request("GET", f"/v1/assets/{symbol}", params=params)
        return AssetDTO.model_validate(data)

    async def get_asset_params(self, account_id: str, symbol: str) -> AssetParamsDTO:
        params = {"account_id": account_id}
        data = await self._request("GET", f"/v1/assets/{symbol}/params", params=params)
        return AssetParamsDTO.model_validate(data)

    async def options_chain(self, underlying_symbol: str) -> OptionsChainDTO:
        data = await self._request("GET", f"/v1/assets/{underlying_symbol}/options")
        return OptionsChainDTO.model_validate(data)

    async def schedule(self, symbol: str) -> SymbolScheduleDTO:
        data = await self._request("GET", f"/v1/assets/{symbol}/schedule")
        return SymbolScheduleDTO.model_validate(data)

    async def cancel_order(self, account_id: str, order_id: str) -> OrderDTO:
        data = await self._request("DELETE", f"/v1/accounts/{account_id}/orders/{order_id}")
        return OrderDTO.model_validate(data)

    async def get_order(self, account_id: str, order_id: str) -> OrderDTO:
        data = await self._request("GET", f"/v1/accounts/{account_id}/orders/{order_id}")
        return OrderDTO.model_validate(data)

    async def get_orders(self, account_id: str) -> GetOrdersDTO:
        data = await self._request("GET", f"/v1/accounts/{account_id}/orders")
        return GetOrdersDTO.model_validate(data)

    async def place_order(self, account_id: str, symbol: str, quantity: str, side: Side, type: OrderType,
                          time_in_force: TimeInForce, limit_price: str, stop_price: str, stop_condition: StopCondition,
                          legs: LegDTO, client_order_id: str, valid_before: ValidBefore, comment: str) -> OrderDTO:
        body: dict[str, Any] = {
            "symbol": symbol,
            "quantity": quantity,
            # Для Enum стараемся отправлять строковые значения, как более совместимые
            "side": getattr(side, "name", side),
            "type": getattr(type, "value", type),
            "time_in_force": getattr(time_in_force, "name", time_in_force),
            "limit_price": limit_price,
            "stop_price": stop_price,
            "stop_condition": getattr(stop_condition, "name", stop_condition),
            "client_order_id": client_order_id,
            "valid_before": getattr(valid_before, "name", valid_before),
            "comment": comment,
        }
        if legs is not None:
            try:
                body["legs"] = [legs.model_dump(exclude_none=True)]
            except Exception:
                body["legs"] = legs  # на случай, если уже словарь

        data = await self._request("POST", f"/v1/accounts/{account_id}/orders", json=body)
        return OrderDTO.model_validate(data)

    async def bars(self, symbol: str, start_time: datetime.datetime, end_time: datetime.datetime,
                   timeframe: TimeFrame) -> BarsRespDTO:
        params = {
            "start_time": start_time,
            "end_time": end_time,
            # Для таймфрейма отдаём имя (TIME_FRAME_M1, ...)
            "timeframe": getattr(timeframe, "name", timeframe),
        }
        data = await self._request("GET", f"/v1/instruments/{symbol}/bars", params=params)
        return BarsRespDTO.model_validate(data)

    async def last_quote(self, symbol: str) -> LastQuoteDTO:
        data = await self._request("GET", f"/v1/instruments/{symbol}/quotes/latest")
        return LastQuoteDTO.model_validate(data)

    async def latest_trades(self, symbol: str) -> LatestTradesDTO:
        data = await self._request("GET", f"/v1/instruments/{symbol}/trades/latest")
        return LatestTradesDTO.model_validate(data)

    async def order_book(self, symbol: str) -> OrderBookRespDTO:
        data = await self._request("GET", f"/v1/instruments/{symbol}/orderbook")
        return OrderBookRespDTO.model_validate(data)