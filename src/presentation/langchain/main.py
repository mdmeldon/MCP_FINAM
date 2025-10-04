import asyncio
import datetime
import json

import pendulum
import streamlit as st
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.prebuilt import create_react_agent as lg_create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from src.configs import LangchainConfig
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)

from src.presentation.langchain.callback import get_streamlit_cb

history = StreamlitChatMessageHistory(key="chat_messages")


@st.cache_resource(show_spinner=False)
def _cached_client(account_id: str, finam_api_token: str):
    with open(".mcp-server-config.json", "r") as file:
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

    client = _cached_client(account_id=account_id, finam_api_token=finam_api_token)

    try:
        tools_from_mcp = await client.get_tools()
        tools.extend(tools_from_mcp)
    except Exception as e:
        st.warning(f"Не удалось загрузить MCP-тулы: {e}")

    agent_graph = lg_create_react_agent(llm, tools)
    return agent_graph


async def _handle_chat_async(agent_graph, messages, callbacks: list, recursion_limit: int = 25):
    config: RunnableConfig = {"callbacks": callbacks, "recursion_limit": recursion_limit}
    return await agent_graph.ainvoke({"messages": messages}, config)


async def _handle_chat_async_stream(agent_graph, messages, callbacks: list, recursion_limit: int = 25) -> str:
    config: RunnableConfig = {"callbacks": callbacks, "recursion_limit": recursion_limit}
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
            finam_api_token = st.text_input("Finam API токен:", value="", help="Оставьте пустым если не требуется")
            account_id = st.text_input("ID счета:", value="", help="Оставьте пустым если не требуется")

    if not finam_api_token:
        st.sidebar.warning(
            "⚠️ Finam API токен не установлен. Установите Finam API token в соответствующем поле."
        )
    else:
        st.sidebar.success("✅ Finam API токен установлен")

    loop = _get_persistent_loop()
    agent_graph = loop.run_until_complete(_init_agent_async(cfg, account_id, finam_api_token))

    if "messages" not in st.session_state:
        st.session_state["messages"] = [AIMessage(content="Чем могу помочь?")]

    for msg in st.session_state.messages:
        if type(msg) == AIMessage:
            st.chat_message("assistant").write(msg.content)
        if type(msg) == HumanMessage:
            st.chat_message("user").write(msg.content)

    if prompt := st.chat_input():
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            st_callback = get_streamlit_cb(st.empty(), expand_steps=True)
            last_msg = loop.run_until_complete(
                _handle_chat_async_stream(agent_graph, st.session_state.messages, [st_callback])
            )
            if last_msg:
                st.session_state.messages.append(AIMessage(content=last_msg))