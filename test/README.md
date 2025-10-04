# Тесты для OPENROUTER

Этот каталог содержит тесты для проверки интеграции с OPENROUTER через langchain.

## Структура

- `test_openrouter.py` - тесты для проверки подключения к OPENROUTER
- `run_test.sh` - скрипт для запуска тестов с использованием `.venv`

## Требования

### Переменные окружения

Создайте файл `.env` в корне проекта со следующими переменными:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### Зависимости

Убедитесь, что установлены следующие пакеты:
- `langchain`
- `langchain-openai`
- `langchain-core`
- `pytest` (для запуска тестов)
- `pytest-asyncio` (для асинхронных тестов)

**Примечание:** Проект использует `uv` в качестве менеджера пакетов.

## Запуск тестов

### Способ 1: Через скрипт (рекомендуется)

```bash
chmod +x test/run_test.sh
./test/run_test.sh
```

### Способ 2: Через uv и pytest напрямую

```bash
# Установите pytest если еще не установлен
uv pip install pytest pytest-asyncio

# Запустите тесты
uv run pytest test/test_openrouter.py -v -s
```

### Способ 3: Запуск как Python скрипт

```bash
# Запустите напрямую через uv
uv run python test/test_openrouter.py
```

## Описание тестов

### `test_openrouter_connection()`
Синхронный тест, который:
- Загружает конфигурацию из переменных окружения
- Создает ChatOpenAI клиент
- Отправляет простой запрос
- Проверяет получение ответа

### `test_openrouter_async()`
Асинхронный тест, который проверяет работу асинхронных запросов к OPENROUTER.

### `test_openrouter_streaming()`
Тест потоковой передачи данных, который:
- Отправляет запрос с включенным streaming
- Получает ответ по частям (chunks)
- Собирает полный ответ

## Примеры вывода

При успешном выполнении вы увидите:

```
🔧 Конфигурация:
   BASE_URL: https://openrouter.ai/api/v1
   MODEL: openai/gpt-4o-mini
   API_KEY: **********...ab12

📤 Отправляем сообщение: Привет! Ответь одним словом: работает ли соединение?

📥 Получен ответ: Да!

✅ Тест успешно пройден!
```

## Устранение проблем

### Ошибка: "OPENROUTER_API_KEY не установлен"
Проверьте наличие файла `.env` в корне проекта и правильность переменных окружения.

### Ошибка: "No module named 'pytest'"
Установите pytest:
```bash
pip install pytest pytest-asyncio
```

### Ошибка: "No module named 'langchain_openai'"
Установите зависимости проекта:
```bash
pip install -e .
```

