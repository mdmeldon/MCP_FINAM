import asyncio

import streamlit as st
from langchain import hub
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.prebuilt import create_react_agent as lg_create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import AgentExecutor, create_react_agent
from src.configs import LangchainConfig
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)

from src.presentation.langchain.callback import get_streamlit_cb

history = StreamlitChatMessageHistory(key="chat_messages")


@st.cache_resource(show_spinner=False)
def _cached_client(account_id: str, finam_api_token: str):
    # Отдельный event loop не создаём; Streamlit управляет петлёй
    return MultiServerMCPClient(
        {
            "finam_mcp": {
                "transport": "stdio",
                "command": "uvx",
                "args": [
                    "--isolated",
                    "--verbose",
                    "--from",
                    "git+ssh://git@github.com/mdmeldon/finam-mcp.git",
                    "finam_mcp"
                ],
                "env": {
                    "FINAM_API_TOKEN": finam_api_token,
                    "FINAM_ACCOUNT_ID": account_id,
                },
                # "transport": "streamable_http",
                # "url": "http://localhost:8000/mcp",
                # "headers": {
                #     # Вынести в конфиг/секреты при необходимости
                #     "Authorization": "Bearer 89b64bdf6c3f4ea36fe80de8f0dac1958175289a4b4bec6d79f97ec7435a9676",
                # },
            }
        }
    )


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
    def get_account_id() -> str | None:
        """Возвращает выбранный пользователем account_id из UI (или пустую строку)."""
        return account_id

    @tool
    def get_finam_api_token() -> str | None:
        """Возвращает введённый пользователем Finam API token из UI (или пустую строку)."""
        return finam_api_token

    tools = load_tools(["ddg-search"])
    tools.append(get_account_id)
    tools.append(get_finam_api_token)

    client = _cached_client(account_id=account_id, finam_api_token=finam_api_token)

    try:
        tools_from_mcp = await client.get_tools()
        tools.extend(tools_from_mcp)
    except Exception as e:
        st.warning(f"Не удалось загрузить MCP-тулы: {e}")

    # agent_graph = lg_create_react_agent(llm, tools)
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt=prompt)
    agent_graph = AgentExecutor(agent=agent, tools=tools, verbose=True)
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
        account_id = st.text_input("ID счета:", value="", help="Оставьте пустым если не требуется")
        finam_api_token = st.text_input("Finam API-token:", value="", help="Оставьте пустым если не требуется")
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
            st_callback = StreamlitCallbackHandler(st.container())
            # st_callback = get_streamlit_cb(st.empty(), expand_steps=True)
            # last_msg = loop.run_until_complete(
            #     _handle_chat_async_stream(agent_graph, st.session_state.messages, [st_callback])
            # )
            last_msg = agent_graph.invoke(
                {"input": st.session_state.messages}, {"callbacks": [st_callback]}
            )
            if last_msg:
                st.session_state.messages.append(AIMessage(content=last_msg["output"]))