"""
Тест для проверки запроса к OPENROUTER через langchain
"""
import os
import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.configs import LangchainConfig


def test_openrouter_connection():
    """
    Тест проверяет возможность подключения к OPENROUTER и получения ответа.
    Использует переменные окружения:
    - OPENROUTER_API_KEY
    - OPENROUTER_BASE_URL
    - OPENROUTER_MODEL
    """
    # Загружаем конфигурацию из переменных окружения
    cfg = LangchainConfig()

    # Проверяем, что все необходимые переменные установлены
    assert cfg.API_KEY.get_secret_value(), "OPENROUTER_API_KEY не установлен"
    assert cfg.BASE_URL, "OPENROUTER_BASE_URL не установлен"
    assert cfg.MODEL, "OPENROUTER_MODEL не установлен"

    print(f"\n🔧 Конфигурация:")
    print(f"   BASE_URL: {cfg.BASE_URL}")
    print(f"   MODEL: {cfg.MODEL}")
    print(f"   API_KEY: {'*' * 10}...{cfg.API_KEY.get_secret_value()[-4:]}")

    # Создаем ChatOpenAI клиент
    llm = ChatOpenAI(
        api_key=cfg.API_KEY.get_secret_value(),
        base_url=cfg.BASE_URL,
        model=cfg.MODEL,
        temperature=0.7,
    )

    # Выполняем простой запрос
    test_message = "Привет! Ответь одним словом: работает ли соединение?"
    print(f"\n📤 Отправляем сообщение: {test_message}")

    messages = [HumanMessage(content=test_message)]
    response = llm.invoke(messages)

    # Проверяем ответ
    assert response is not None, "Ответ не получен"
    assert response.content, "Содержимое ответа пустое"

    print(f"\n📥 Получен ответ: {response.content}")
    print(f"\n✅ Тест успешно пройден!")


@pytest.mark.asyncio
async def test_openrouter_async():
    """
    Асинхронный тест для проверки запроса к OPENROUTER.
    """
    # Загружаем конфигурацию
    cfg = LangchainConfig()

    # Создаем ChatOpenAI клиент
    llm = ChatOpenAI(
        api_key=cfg.API_KEY.get_secret_value(),
        base_url=cfg.BASE_URL,
        model=cfg.MODEL,
        temperature=0.7,
    )

    # Выполняем асинхронный запрос
    test_message = "Посчитай 2+2 и ответь числом"
    print(f"\n📤 Асинхронный запрос: {test_message}")

    messages = [HumanMessage(content=test_message)]
    response = await llm.ainvoke(messages)

    # Проверяем ответ
    assert response is not None
    assert response.content

    print(f"\n📥 Асинхронный ответ: {response.content}")
    print(f"\n✅ Асинхронный тест успешно пройден!")


def test_openrouter_streaming():
    """
    Тест для проверки потокового ответа от OPENROUTER.
    """
    cfg = LangchainConfig()

    llm = ChatOpenAI(
        api_key=cfg.API_KEY.get_secret_value(),
        base_url=cfg.BASE_URL,
        model=cfg.MODEL,
        temperature=0.7,
        streaming=True,
    )

    test_message = "Перечисли три цвета через запятую"
    print(f"\n📤 Потоковый запрос: {test_message}")

    messages = [HumanMessage(content=test_message)]

    # Собираем потоковый ответ
    chunks = []
    print("\n📥 Получаем потоковый ответ:")
    for chunk in llm.stream(messages):
        if chunk.content:
            chunks.append(chunk.content)
            print(chunk.content, end="", flush=True)

    full_response = "".join(chunks)
    print()  # Новая строка после потока

    # Проверяем, что получили ответ
    assert len(chunks) > 0, "Потоковый ответ пустой"
    assert full_response, "Полный ответ пустой"

    print(f"\n✅ Потоковый тест успешно пройден!")
    print(f"   Получено чанков: {len(chunks)}")


if __name__ == "__main__":
    # Запуск тестов напрямую (без pytest)
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К OPENROUTER")
    print("=" * 60)

    try:
        print("\n" + "=" * 60)
        print("1. СИНХРОННЫЙ ТЕСТ")
        print("=" * 60)
        test_openrouter_connection()

        print("\n" + "=" * 60)
        print("2. ПОТОКОВЫЙ ТЕСТ")
        print("=" * 60)
        test_openrouter_streaming()

        print("\n" + "=" * 60)
        print("3. АСИНХРОННЫЙ ТЕСТ")
        print("=" * 60)
        import asyncio
        asyncio.run(test_openrouter_async())

        print("\n" + "=" * 60)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
