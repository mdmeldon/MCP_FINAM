import asyncio
import datetime
import json

import pendulum
import streamlit as st
import plotly.graph_objects as go
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.prebuilt import create_react_agent as lg_create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from src.configs import LangchainConfig
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)

from src.presentation.langchain.callback import get_streamlit_cb
from src.presentation.langchain.tools.visualization import (
    visualize_portfolio,
    visualize_strategy_backtest,
    create_comparison_chart,
)

history = StreamlitChatMessageHistory(key="chat_messages")


@st.cache_resource(show_spinner=False)
def _cached_client(account_id: str, finam_api_token: str):
    with open("git.mcp-server-config.json", "r") as file:
        config = json.loads(file.read())

        if config["finam_mcp"]["transport"] == "stdio":
            config["finam_mcp"]["env"] = {
                "FINAM_API_TOKEN": finam_api_token,
                "FINAM_ACCOUNT_ID": account_id,
            }
        return MultiServerMCPClient(config)


@st.cache_resource(show_spinner=False)
def _cached_llm(cfg: LangchainConfig):
    return ChatOpenAI(
        api_key=cfg.API_KEY,
        base_url=cfg.BASE_URL,
        model=cfg.MODEL,
        streaming=True,
    )


async def _init_agent_async(cfg: LangchainConfig, account_id: str, finam_api_token: str):
    """Инициализировать LangGraph-агент и инструменты асинхронно (в т.ч. MCP)."""
    llm = _cached_llm(cfg)

    @tool
    def get_current_time(tz: str = "UTC") -> pendulum.DateTime:
        """ВАЖНО! Если запрос пользователя связан с датой/временем обязательно нужно проверить текущее время!"""
        return pendulum.now(tz)

    tools = load_tools(["ddg-search"])
    tools.append(get_current_time)

    # Добавляем инструменты визуализации
    tools.extend([
        visualize_portfolio,
        visualize_strategy_backtest,
        create_comparison_chart,
    ])

    client = _cached_client(account_id=account_id,
                            finam_api_token=finam_api_token)

    try:
        tools_from_mcp = await client.get_tools()
        tools.extend(tools_from_mcp)
    except Exception as e:
        st.warning(f"Не удалось загрузить MCP-тулы: {e}")

    # Системный промпт с инструкциями по визуализации
    system_message = SystemMessage(content="""Ты - AI-ассистент для работы с финансовыми рынками через Finam Trade API.

🎯 ВАЖНЫЕ ПРАВИЛА ПО ВИЗУАЛИЗАЦИИ:

1. **Анализ портфеля**: При запросе анализа портфеля ВСЕГДА используй:
   - Сначала get_account для получения данных
   - Затем visualize_portfolio для создания Sunburst диаграммы
   
2. **Бэктест стратегии**: При тестировании стратегий ВСЕГДА используй:
   - Сначала bars для получения исторических данных
   - Затем trades для получения/симуляции сделок
   - Затем visualize_strategy_backtest для визуализации результатов

3. **Сравнение инструментов**: При сравнении нескольких акций используй:
   - bars для каждого инструмента
   - create_comparison_chart для сравнительного графика

4. **Формат ответа**: Всегда давай текстовый анализ ВМЕСТЕ с визуализацией, не только график.

Твоя задача - превратить сложные финансовые данные в понятные визуальные инсайты.""")

    agent_graph = lg_create_react_agent(
        llm, tools, prompt=system_message)
    return agent_graph


async def _handle_chat_async(agent_graph, messages, callbacks: list, recursion_limit: int = 25):
    config: RunnableConfig = {"callbacks": callbacks,
                              "recursion_limit": recursion_limit}
    return await agent_graph.ainvoke({"messages": messages}, config)


async def _handle_chat_async_stream(agent_graph, messages, callbacks: list, recursion_limit: int = 25) -> str:
    config: RunnableConfig = {"callbacks": callbacks,
                              "recursion_limit": recursion_limit}
    async for _ in agent_graph.astream({"messages": messages}, config):
        pass
    cb = callbacks[0]
    return getattr(cb, "_answer_accum", "")


def _get_persistent_loop() -> asyncio.AbstractEventLoop:
    loop = st.session_state.get("_persistent_loop")
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        st.session_state["_persistent_loop"] = loop
    return loop


def create_langchain_app(cfg: LangchainConfig):
    with st.sidebar:
        st.title("Finam AI Assistant")
        st.info(f"Модель: {cfg.MODEL}")
        with st.expander("🔑 Доступы:"):
            finam_api_token = st.text_input(
                "Finam API токен:", value="", help="Оставьте пустым если не требуется")
            account_id = st.text_input(
                "ID счета:", value="", help="Оставьте пустым если не требуется")

    if not finam_api_token:
        st.sidebar.warning(
            "⚠️ Finam API токен не установлен. Установите Finam API token в соответствующем поле."
        )
    else:
        st.sidebar.success("✅ Finam API токен установлен")

    loop = _get_persistent_loop()
    agent_graph = loop.run_until_complete(
        _init_agent_async(cfg, account_id, finam_api_token))

    # Инициализация session_state
    if "messages" not in st.session_state:
        st.session_state["messages"] = [AIMessage(content="Чем могу помочь?")]

    if "visualizations" not in st.session_state:
        st.session_state["visualizations"] = []

    # Отображение визуализаций
    if st.session_state.get("visualizations"):
        st.divider()

        # Кнопки управления визуализациями
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📊 Визуализации")
        with col2:
            if st.button("🗑️ Очистить", key="clear_viz"):
                st.session_state["visualizations"] = []
                st.rerun()

        # Отображение графиков
        for idx, viz in enumerate(st.session_state["visualizations"]):
            with st.container():
                st.markdown(f"#### {viz['title']}")
                try:
                    fig = go.Figure(json.loads(viz['data']))
                    st.plotly_chart(
                        fig, use_container_width=True, key=f"viz_{idx}")
                except Exception as e:
                    st.error(f"Ошибка отображения визуализации: {e}")

        st.divider()

    # Отображение истории чата
    for msg in st.session_state.messages:
        if type(msg) == AIMessage:
            st.chat_message("assistant").write(msg.content)
        if type(msg) == HumanMessage:
            st.chat_message("user").write(msg.content)

    if prompt := st.chat_input():
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            # Запоминаем количество визуализаций до обработки
            viz_count_before = len(st.session_state.get("visualizations", []))

            st_callback = get_streamlit_cb(st.empty(), expand_steps=True)
            last_msg = loop.run_until_complete(
                _handle_chat_async_stream(
                    agent_graph, st.session_state.messages, [st_callback])
            )
            if last_msg:
                st.session_state.messages.append(AIMessage(content=last_msg))

            # Если добавились новые визуализации, перезапускаем страницу
            viz_count_after = len(st.session_state.get("visualizations", []))
            if viz_count_after > viz_count_before:
                st.rerun()
