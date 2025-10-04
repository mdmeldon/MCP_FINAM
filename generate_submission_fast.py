#!/usr/bin/env python3
"""
Оптимизированный скрипт для генерации submission.csv

ОПТИМИЗАЦИИ:
- ❌ Без реальных MCP tool calls (прямое предсказание endpoint)
- ✅ Параллельная обработка (батчи по 10-20 запросов)
- ✅ Few-shot learning из train.csv
- ✅ Упрощенный промпт для быстрого ответа

Ожидаемое время: ~1-2 минуты для 312 вопросов (вместо 15-26 минут)

Использование:
    python scripts/generate_submission_fast.py --test-file data/interim/test.csv --output-file data/interim/submission.csv

Опции:
    --test-file PATH      Путь к test.csv
    --output-file PATH    Путь к submission.csv
    --train-file PATH     Путь к train.csv (для few-shot примеров)
    --limit INT           Обработать только первые N вопросов
    --batch-size INT      Размер батча для параллельной обработки (по умолчанию 15)
    --debug               Режим отладки
"""

import asyncio
import csv
import re
import time
from pathlib import Path
from typing import Any

import click
from tqdm import tqdm  # type: ignore[import-untyped]

from typing import Any

import requests


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> dict[str, Any]:
    """Простой вызов LLM без tools"""
    payload: dict[str, Any] = {
        "model": "openai/gpt4o-mini",
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    r = requests.post(
        f"https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer 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",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def calculate_cost(usage: dict, model: str) -> float:
    """Рассчитать стоимость запроса"""
    pricing = {
        "openai/gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "openai/gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "google/gemini-2.5-flash": {"prompt": 0.10, "completion": 0.40},
        "anthropic/claude-3-sonnet": {"prompt": 3.00, "completion": 15.00},
        "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    }
    prices = pricing.get(model, {"prompt": 0.10, "completion": 0.40})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    prompt_cost = (prompt_tokens / 1_000_000) * prices["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * prices["completion"]

    return prompt_cost + completion_cost


def create_optimized_prompt(examples: list[dict[str, str]]) -> str:
    """
    Создать оптимизированный промпт с few-shot примерами.

    Формат: вопрос -> прямой ответ в формате "METHOD /path"
    """
    # Берем первые 15 примеров для few-shot
    few_shot_examples = examples[:15]

    examples_text = "\n".join([
        f"Вопрос: {ex['question']}\nОтвет: {ex['type']} {ex['request']}\n"
        for ex in few_shot_examples
    ])

    return f"""Ты - эксперт по Finam TradeAPI. Преобразуй вопрос в HTTP запрос.

ФОРМАТ ОТВЕТА - ТОЛЬКО ТАК:
METHOD /path

Текущая дата: 2025-10-04

Где:
- METHOD: GET, POST, DELETE
- /path: путь к API endpoint

ПРИМЕРЫ:

{examples_text}

ВАЖНО:
1. Отвечай ТОЛЬКО в формате "METHOD /path"
2. Не добавляй объяснений, комментариев
3. Используй {{account_id}}, {{order_id}} для параметров
4. Символы: SBER@MISX, GAZP@MISX, ROSN@MISX, LKOH@MISX, etc.

ПРАВИЛА ФОРМИРОВАНИЯ QUERY-ПАРАМЕТРОВ:
— Все даты/время: ISO8601 с таймзоной UTC (например, 2025-10-04T00:00:00Z)
— Таймфрейм: имя enum (например, TIME_FRAME_M5)
— Если параметр обязателен для фильтра, включай его в строку запроса после ? через &
— Не добавляй параметры, если по вопросу они не требуются
— Будь крайне внимателен при формировании запросов

По эндпоинтам:
- GET /v1/accounts/{{account_id}}/trades?interval.start_time=...&interval.end_time=...&limit=...
- GET /v1/accounts/{{account_id}}/transactions?interval.start_time=...&interval.end_time=...&limit=...
- GET /v1/instruments/{{symbol}}/bars?interval.start_time=...&interval.end_time=...&timeframe=...
- GET /v1/assets?symbol=...&ticker=...&mic=...&name=...&type=...&limit=...&offset=...
- GET /v1/assets/{{symbol}}?account_id={{account_id}}
- GET /v1/assets/{{symbol}}/params?account_id={{account_id}}
- GET /v1/assets/{{symbol}}/schedule   (без query)
- GET /v1/assets/{{underlying_symbol}}/options   (без query)
- GET /v1/instruments/{{symbol}}/quotes/latest   (без query)
- GET /v1/instruments/{{symbol}}/trades/latest   (без query)
- GET /v1/instruments/{{symbol}}/orderbook   (без query)
- GET /v1/accounts/{{account_id}}   (без query)
- GET /v1/accounts/{{account_id}}/orders   (без query)
- GET /v1/accounts/{{account_id}}/orders/{{order_id}}   (без query)
- DELETE /v1/accounts/{{account_id}}/orders/{{order_id}}   (без query)
- POST /v1/accounts/{{account_id}}/orders   (тело JSON, без query)

ШАБЛОНЫ ENDPOINTS (синхронизированы с серверными handlers):

Котировки/данные:
GET /v1/instruments/{{symbol}}/quotes/latest
GET /v1/instruments/{{symbol}}/orderbook
GET /v1/instruments/{{symbol}}/trades/latest
GET /v1/instruments/{{symbol}}/bars

Инструменты:
GET /v1/assets
GET /v1/assets/{{symbol}}
GET /v1/assets/{{symbol}}/params
GET /v1/assets/{{symbol}}/schedule
GET /v1/assets/{{symbol}}/options

Счет/ордера:
GET /v1/accounts/{{account_id}}
GET /v1/accounts/{{account_id}}/orders
GET /v1/accounts/{{account_id}}/orders/{{order_id}}
POST /v1/accounts/{{account_id}}/orders
DELETE /v1/accounts/{{account_id}}/orders/{{order_id}}
GET /v1/accounts/{{account_id}}/trades
GET /v1/accounts/{{account_id}}/transactions

Служебные:
GET /v1/assets/clock
GET /v1/exchanges"""


def parse_api_response(response_text: str) -> tuple[str, str]:
    """
    Извлечь METHOD и path из ответа LLM.

    Ожидаемый формат: "METHOD /path"

    Returns:
        tuple: (method, path)
    """
    # Паттерн: METHOD /path
    pattern = r'(GET|POST|DELETE|PUT|PATCH)\s+(/[^\s\n]+)'
    match = re.search(pattern, response_text, re.IGNORECASE)

    if match:
        method = match.group(1).upper()
        path = match.group(2)
        return method, path

    # Fallback
    return "GET", "/v1/assets"


async def generate_api_call_fast(
    question: str,
    system_prompt: str,
    model: str,
    debug: bool = False
) -> tuple[dict[str, str], float]:
    """
    Быстрая генерация API запроса БЕЗ MCP tools.

    Returns:
        tuple: ({"type": method, "request": path}, cost)
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Вопрос: {question}\nОтвет:"}
    ]

    try:
        # Вызываем LLM БЕЗ MCP tools
        response = await call_llm_async(
            messages,
            temperature=0.0,
            use_mcp_tools=False  # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ
        )

        # Извлекаем ответ
        content = response["choices"][0]["message"].get("content", "")

        if debug:
            click.echo(f"  LLM ответ: {content}")

        # Парсим METHOD и path
        method, path = parse_api_response(content)

        # Рассчитываем стоимость
        usage = response.get("usage", {})
        cost = calculate_cost(usage, model)

        return {"type": method, "request": path}, cost

    except Exception as e:
        if debug:
            click.echo(f"  ❌ Ошибка: {e}")
        return {"type": "GET", "request": "/v1/assets"}, 0.0


async def process_batch(
    batch: list[dict[str, str]],
    system_prompt: str,
    model: str,
    debug: bool = False
) -> list[tuple[dict[str, str], float]]:
    """
    Обработать батч вопросов параллельно.

    Returns:
        list: [(api_call, cost), ...]
    """
    tasks = [
        generate_api_call_fast(item["question"], system_prompt, model, debug)
        for item in batch
    ]

    # Параллельное выполнение
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обработка результатов
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            # Fallback при ошибке
            processed_results.append(
                ({"type": "GET", "request": "/v1/assets"}, 0.0))
        else:
            processed_results.append(result)

    return processed_results


@click.command()
@click.option(
    "--test-file",
    type=click.Path(exists=True, path_type=Path),
    default="./test.csv",
    help="Путь к test.csv",
)
@click.option(
    "--output-file",
    type=click.Path(path_type=Path),
    default="submission.csv",
    help="Путь к submission.csv",
)
@click.option(
    "--train-file",
    type=click.Path(exists=True, path_type=Path),
    default="./train.csv",
    help="Путь к train.csv (для few-shot примеров)",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Обработать только первые N вопросов",
)
@click.option(
    "--batch-size",
    type=int,
    default=15,
    help="Размер батча для параллельной обработки",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Режим отладки",
)
def main(
    test_file: Path,
    output_file: Path,
    train_file: Path,
    limit: int | None,
    batch_size: int,
    debug: bool
) -> None:
    """🚀 Быстрая генерация submission файла (оптимизированная версия)"""

    click.echo("🚀 Быстрая генерация submission файла...")
    click.echo("⚡ ОПТИМИЗАЦИИ: без MCP tools + параллелизация\n")

    # Получаем настройки
    model = "openai/gpt4o-mini"

    click.echo(f"🤖 Модель: {model}")
    click.echo(f"📦 Размер батча: {batch_size}")

    # Читаем train.csv для few-shot примеров
    click.echo(f"\n📚 Загрузка примеров из {train_file}...")
    train_examples = []
    with open(train_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            train_examples.append({
                "question": row["question"],
                "type": row["type"],
                "request": row["request"]
            })

    click.echo(f"✅ Загружено {len(train_examples)} примеров")

    # Создаем системный промпт
    system_prompt = create_optimized_prompt(train_examples)

    # Читаем тестовый набор
    click.echo(f"\n📖 Чтение {test_file}...")
    test_questions = []
    with open(test_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            test_questions.append({
                "uid": row["uid"],
                "question": row["question"]
            })

    # Применяем лимит
    if limit:
        test_questions = test_questions[:limit]
        click.echo(f"⚠️  Тестовый режим: только первые {limit} вопросов")

    click.echo(f"✅ Найдено {len(test_questions)} вопросов\n")

    # Генерация ответов
    async def process_all():
        results = []
        total_cost = 0.0
        start_time = time.time()

        # Разбиваем на батчи
        batches = [
            test_questions[i:i + batch_size]
            for i in range(0, len(test_questions), batch_size)
        ]

        click.echo(
            f"🔄 Обработка {len(batches)} батчей по {batch_size} вопросов...")

        for batch in tqdm(batches, desc="Батчи", disable=debug):
            if debug:
                click.echo(f"\n📦 Батч ({len(batch)} вопросов):")
                for item in batch:
                    click.echo(f"  - {item['question']}")

            # Обрабатываем батч параллельно
            batch_results = await process_batch(batch, system_prompt, model, debug)

            # Собираем результаты
            for item, (api_call, cost) in zip(batch, batch_results):
                results.append({
                    "uid": item["uid"],
                    "type": api_call["type"],
                    "request": api_call["request"]
                })
                total_cost += cost

                if debug:
                    click.echo(
                        f"    ✅ {api_call['type']} {api_call['request']}")

        elapsed_time = time.time() - start_time

        return results, total_cost, elapsed_time

    # Запускаем асинхронную обработку
    click.echo("🤖 Генерация API запросов...\n")
    results, total_cost, elapsed_time = asyncio.run(process_all())

    # Сохраняем результаты
    click.echo(f"\n💾 Сохранение в {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["uid", "type", "request"], delimiter=";"
        )
        writer.writeheader()
        writer.writerows(results)

    # Статистика
    click.echo(f"\n✅ Готово! Создано {len(results)} записей")
    click.echo(f"\n⏱️  ПРОИЗВОДИТЕЛЬНОСТЬ:")
    click.echo(
        f"   Общее время: {elapsed_time:.1f} сек ({elapsed_time/60:.1f} мин)")
    click.echo(
        f"   Среднее время на вопрос: {elapsed_time/len(results):.2f} сек")
    click.echo(f"   Вопросов в секунду: {len(results)/elapsed_time:.1f}")

    click.echo(f"\n💰 СТОИМОСТЬ:")
    click.echo(f"   Общая: ${total_cost:.4f}")
    click.echo(f"   На запрос: ${total_cost/len(results):.6f}")

    # Статистика по типам
    click.echo("\n📊 Статистика по типам:")
    type_counts: dict[str, int] = {}
    for r in results:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
    for method, count in sorted(type_counts.items()):
        percentage = (count / len(results)) * 100
        click.echo(f"   {method}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
