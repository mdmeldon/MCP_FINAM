#!/bin/bash
# Скрипт для запуска тестов OPENROUTER с использованием .venv окружения и uv

echo "🚀 Запуск тестов OPENROUTER..."
echo ""

# Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_DIR/.venv"

# Проверяем наличие uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv не найден!"
    echo "   Установите uv: https://docs.astral.sh/uv/"
    exit 1
fi

# Проверяем наличие .venv
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Виртуальное окружение .venv не найдено!"
    echo "   Путь: $VENV_PATH"
    echo ""
    echo "Создайте виртуальное окружение командой:"
    echo "  uv venv"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "⚠️  Файл .env не найден в корне проекта!"
    echo "   Убедитесь, что у вас есть .env файл с переменными:"
    echo "   - OPENROUTER_API_KEY"
    echo "   - OPENROUTER_BASE_URL"
    echo "   - OPENROUTER_MODEL"
    echo ""
fi

# Переходим в директорию проекта
cd "$PROJECT_DIR"

echo ""
echo "=========================================================="
echo "Запуск тестов..."
echo "=========================================================="
echo ""

# Проверяем наличие pytest
echo "📦 Проверяем зависимости..."
uv pip list | grep pytest > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  pytest не установлен. Устанавливаем..."
    uv pip install pytest pytest-asyncio
fi

# Запускаем тесты через uv
echo ""
echo "🧪 Запуск тестов..."
uv run pytest test/test_openrouter.py -v -s

# Раскомментируйте для запуска напрямую через Python:
# uv run python test/test_openrouter.py

echo ""
echo "✅ Готово!"

