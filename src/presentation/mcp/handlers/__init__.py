from mcp.server.fastmcp import FastMCP

from .client import (
    finam_auth,
    finam_token_details,
    get_account,
    trades,
    transactions,
    assets,
    clock,
    exchanges,
    get_asset,
    get_asset_params,
    options_chain,
    schedule,
    cancel_order,
    get_order,
    get_orders,
    place_order,
    bars,
    last_quote,
    latest_trades,
    order_book,
)


def init_tools(app: FastMCP) -> None:
    # Auth
    # app.add_tool(finam_auth, name="finam_auth", title="Authenticate with API token and get JWT")
    # app.add_tool(finam_token_details, name="finam_token_details", title="Get JWT token details")

    # Accounts & portfolio
    app.add_tool(get_account, name="get_account", title="Get account by id")
    app.add_tool(trades, name="trades", title="Get account trades history")
    app.add_tool(transactions, name="transactions", title="Get account transactions")

    # Reference data
    app.add_tool(assets, name="assets", title="List assets")
    app.add_tool(clock, name="clock", title="Get server time")
    app.add_tool(exchanges, name="exchanges", title="List exchanges")
    app.add_tool(get_asset, name="get_asset", title="Get asset by symbol")
    app.add_tool(get_asset_params, name="get_asset_params", title="Get asset trading params")
    app.add_tool(options_chain, name="options_chain", title="Get options chain for underlying")
    app.add_tool(schedule, name="schedule", title="Get trading schedule for symbol")

    # Orders
    app.add_tool(cancel_order, name="cancel_order", title="Cancel order")
    app.add_tool(get_order, name="get_order", title="Get order by id")
    app.add_tool(get_orders, name="get_orders", title="List account orders")
    app.add_tool(place_order, name="place_order", title="Place new order")

    # Market data
    app.add_tool(bars, name="bars", title="Get historical bars")
    app.add_tool(last_quote, name="last_quote", title="Get last quote")
    app.add_tool(latest_trades, name="latest_trades", title="Get latest trades")
    app.add_tool(order_book, name="order_book", title="Get order book")