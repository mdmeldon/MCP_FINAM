from typing import Callable, TypeVar
import time

from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.delta_generator import DeltaGenerator

from langchain_core.callbacks.base import BaseCallbackHandler
try:
    # Для логов размышлений агента (Thought/Action/Observation)
    from langchain_core.agents import AgentAction, AgentFinish  # type: ignore
except Exception:  # pragma: no cover
    AgentAction = object  # type: ignore
    AgentFinish = object  # type: ignore


class StreamlitGraphCallbackHandler(BaseCallbackHandler):
    """
    Потоковый обработчик для LangGraph/LangChain, безопасный для Streamlit.

    - Выводит генерируемые токены LLM в реальном времени
    - Показывает шаги цепочки/графа и вызовы тулов
    - Отображает ошибки

    Важно: принудительно добавляет контекст выполнения Streamlit для каждого коллбэка,
    чтобы исключить NoSessionContext.
    """

    def __init__(self, parent_container: DeltaGenerator, *,
                 expand_answer: bool = True,
                 expand_steps: bool = False,
                 **_: object):
        super().__init__()
        self._ctx = get_script_run_ctx()

        # Разметка: только выпадашки для размышлений и финальный ответ
        self._root = parent_container.container()
        # Контейнер для итераций размышлений (каждая итерация — отдельный expander)
        self._iters_root = self._root.container()
        self._current_step = None  # type: ignore[var-annotated]
        self._current_step_idx: int | None = None
        self._step_index = 1
        # Состояния шагов: expander и плейсхолдер статуса на его вершине
        self._steps: list[dict] = []
        self._expand_steps = expand_steps
        self._pending_thoughts: list[str] = []

        # Ниже — финальный ответ (всегда внизу блока)
        self._root.markdown("**Ответ:**")
        self._answer_box = self._root.empty()

        # Буфер токенов и частота обновления
        self._token_buf: list[str] = []
        self._last_flush = 0.0
        self._flush_every_tokens = 1
        self._flush_every_sec = 0.03
        self._answer_accum: str = ""

    # Вспомогательная обёртка контекста
    def _with_ctx(self, fn: Callable[[], None]) -> None:
        add_script_run_ctx(ctx=self._ctx)
        fn()

    # ===== LLM events =====
    def on_llm_start(self, *args, **kwargs) -> None:
        def _():
            self._token_buf.clear()
            self._answer_accum = ""
            self._answer_box.markdown("")
        self._with_ctx(_)

    def on_llm_new_token(self, token: str, *args, **kwargs) -> None:
        self._token_buf.append(token)

        now = time.time()
        should_flush = (
            len(self._token_buf) >= self._flush_every_tokens or
            (now - self._last_flush) >= self._flush_every_sec
        )
        if not should_flush:
            return

        # Накопим и перерисуем целиком
        self._answer_accum += "".join(self._token_buf)
        self._token_buf.clear()
        self._last_flush = now

        def _():
            self._answer_box.markdown(self._answer_accum, unsafe_allow_html=False)
        self._with_ctx(_)

    def on_llm_end(self, *args, **kwargs) -> None:
        # Дофлашим остатки (перерисуем целиком)
        if self._token_buf:
            self._answer_accum += "".join(self._token_buf)
            self._token_buf.clear()

            def _():
                self._answer_box.markdown(self._answer_accum)
            self._with_ctx(_)

    def on_llm_error(self, error: BaseException, *args, **kwargs) -> None:
        # Ошибки не выделяем в отдельную выпадашку, можно писать в текущую
        def _():
            target = self._current_step or self._iters_root
            target.markdown(f"**LLM error:** {error}")
        self._with_ctx(_)

    # ===== Chain / Graph events =====
    def on_chain_start(self, serialized, inputs, *args, **kwargs) -> None:
        # Не отображаем отдельным блоком
        return None

    def on_chain_end(self, outputs, *args, **kwargs) -> None:
        return None

    def on_chain_error(self, error: BaseException, *args, **kwargs) -> None:
        def _():
            target = self._current_step or self._iters_root
            target.markdown(f"**Chain error:** {error}")
        self._with_ctx(_)

    # ===== Tools =====
    def on_tool_start(self, serialized, input_str, *args, **kwargs) -> None:
        name = (serialized or {}).get("name", "tool")
        preview = input_str if isinstance(input_str, str) else str(input_str)
        if len(preview) > 500:
            preview = preview[:500] + "…"

        def _():
            # Если итерация ещё не создана (LangGraph без AgentAction), создадим её здесь
            if self._current_step is None:
                exp = self._iters_root.expander(f"Итерация {self._step_index}", expanded=self._expand_steps)
                status_ph = exp.empty()
                self._current_step = exp
                self._current_step_idx = len(self._steps)
                self._steps.append({"exp": exp, "status": status_ph, "tools": []})
                # Если есть накопленные размышления — выведем их
                if self._pending_thoughts:
                    for t in self._pending_thoughts:
                        exp.markdown(f"```text\n{t}\n```")
                    self._pending_thoughts.clear()
                self._step_index += 1

            # Обновим статус текущей итерации как выполняющийся инструмент
            if self._current_step_idx is not None and self._current_step_idx < len(self._steps):
                step = self._steps[self._current_step_idx]
                step["status"].markdown(f"🟡 Выполняется инструмент: `{name}`…")
                tool_block_ph = step["exp"].empty()
                tool_block_exp = tool_block_ph.expander(f"{name} — 🟡 Выполняется", expanded=False)
                tool_block_exp.markdown(f"**Вход:**\n\n```\n{preview}\n```")
                step["tools"].append({
                    "name": name,
                    "status": "running",
                    "ph": tool_block_ph,
                    "input": input_str,
                })
        self._with_ctx(_)

    def on_tool_end(self, output, *args, **kwargs) -> None:
        out = output if isinstance(output, str) else str(output)
        if len(out) > 2000:
            out = out[:2000] + "…"

        def _():
            if self._current_step_idx is not None and self._current_step_idx < len(self._steps):
                step = self._steps[self._current_step_idx]
                # пометим итерацию как успешную
                step["status"].markdown("🟢 Инструмент завершён успешно")
                tools_list = step.get("tools", [])
                if tools_list:
                    tool_info = tools_list[-1]
                    name = tool_info.get("name", "tool")
                    ph = tool_info["ph"]
                    tool_info["status"] = "success"
                    # переотрисуем экспандер с новым заголовком и контентом
                    ph.empty()
                    exp = ph.expander(f"{name} — 🟢 Успешно", expanded=False)
                    exp.markdown(f"**Вход:**\n\n```\n{tool_info.get('input','')}\n```")
                    exp.markdown(f"**Результат:**\n\n```\n{out}\n```")
        self._with_ctx(_)

    def on_tool_error(self, error: BaseException, *args, **kwargs) -> None:
        def _():
            if self._current_step_idx is not None and self._current_step_idx < len(self._steps):
                step = self._steps[self._current_step_idx]
                step["status"].markdown(f"🔴 Ошибка инструмента: {error}")
                tools_list = step.get("tools", [])
                if tools_list:
                    tool_info = tools_list[-1]
                    name = tool_info.get("name", "tool")
                    ph = tool_info["ph"]
                    tool_info["status"] = "error"
                    ph.empty()
                    exp = ph.expander(f"{name} — 🔴 Ошибка", expanded=False)
                    exp.markdown(f"**Вход:**\n\n```\n{tool_info.get('input','')}\n```")
                    exp.markdown(f"**Ошибка:** {error}")
        self._with_ctx(_)

    # ===== Agent reasoning (Thought / Action / Observation logs) =====
    def on_agent_action(self, action: AgentAction, *args, **kwargs) -> None:  # type: ignore[override]
        log_text = getattr(action, "log", "") or ""
        tool = getattr(action, "tool", "") or ""
        tool_input = getattr(action, "tool_input", "")
        tool_input_str = tool_input if isinstance(tool_input, str) else str(tool_input)
        if len(tool_input_str) > 1000:
            tool_input_str = tool_input_str[:1000] + "…"

        def _():
            # Создаём отдельный expander для каждой итерации (если его ещё нет)
            exp = self._iters_root.expander(f"Итерация {self._step_index}", expanded=self._expand_steps)
            status_ph = exp.empty()
            self._current_step = exp
            self._current_step_idx = len(self._steps)
            self._steps.append({"exp": exp, "status": status_ph, "tools": []})
            if log_text:
                exp.markdown(f"```text\n{log_text}\n```")
            if tool:
                exp.markdown(f"Будет вызван инструмент: `{tool}`\n\n```\n{tool_input_str}\n```")
            self._step_index += 1
        self._with_ctx(_)

    def on_agent_finish(self, finish: AgentFinish, *args, **kwargs) -> None:  # type: ignore[override]
        log_text = getattr(finish, "log", "") or ""

        def _():
            # Пишем завершение в последний активный шаг, либо создаём отдельный
            target = self._current_step or self._iters_root.expander("Завершение", expanded=False)
            if log_text:
                target.markdown(f"```text\n{log_text}\n```")
        self._with_ctx(_)


def get_streamlit_cb(parent_container: DeltaGenerator,
                     *,
                     expand_answer: bool = True,
                     expand_steps: bool = False,
                     **kwargs: object) -> BaseCallbackHandler:
    """
    Возвращает улучшенный коллбэк для потоковой интеграции LangGraph в Streamlit.
    """
    return StreamlitGraphCallbackHandler(
        parent_container,
        expand_answer=expand_answer,
        expand_steps=expand_steps,
    )