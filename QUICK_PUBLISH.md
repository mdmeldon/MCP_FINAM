# 🚀 Быстрая публикация на PyPI - Шпаргалка

## Перед началом

1. ✅ Зарегистрируйтесь на [pypi.org](https://pypi.org/account/register/)
2. ✅ Создайте [API токен](https://pypi.org/manage/account/token/)
3. ✅ Обновите `pyproject.toml` (имя, email, URL репозитория)

## Пошаговая публикация

### Шаг 1: Установите необходимые инструменты

```bash
uv pip install build twine
```

### Шаг 2: Очистите и соберите пакет

```bash
cd /Users/graph/services/Pet_projects/mcp/Finam

# Очистка
rm -rf dist/ build/ *.egg-info

# Сборка
python -m build
```

### Шаг 3: Проверьте пакет

```bash
# Проверка структуры
twine check dist/*

# Локальное тестирование
uv pip install dist/*.whl
finam-mcp --help
```

### Шаг 4: Опубликуйте на PyPI

```bash
twine upload dist/*

# Введите:
# Username: __token__
# Password: pypi-AgEI... (ваш токен)
```

### Шаг 5: Проверьте публикацию

```bash
# Проверьте на сайте
open https://pypi.org/project/finam-mcp/

# Протестируйте через uvx
uvx finam-mcp
```

## Быстрые команды для обновления

```bash
# 1. Обновите версию в pyproject.toml
# [project]
# version = "0.1.1"

# 2. Пересоберите
rm -rf dist/ && python -m build

# 3. Опубликуйте
twine upload dist/*
```

## Использование после публикации

Пользователи смогут запускать ваш сервер так:

```bash
# Через uvx (без установки)
uvx finam-mcp
```

В конфигурации Claude/Cursor:

```json
{
  "mcpServers": {
    "finam": {
      "command": "uvx",
      "args": ["finam-mcp"]
    }
  }
}
```

## Устранение проблем

| Проблема               | Решение                                           |
| ---------------------- | ------------------------------------------------- |
| Package already exists | Увеличьте версию в `pyproject.toml`               |
| Invalid credentials    | Проверьте токен, username должен быть `__token__` |
| Name taken             | Измените `name` в `pyproject.toml`                |
| uvx не находит         | Подождите 1-2 минуты, проверьте имя пакета        |

## Полезные ссылки

- 📖 [Подробное руководство](PUBLISHING_GUIDE.md)
- 🌐 [PyPI](https://pypi.org/)
- 🔑 [Управление токенами](https://pypi.org/manage/account/token/)

---

**Готово!** Ваш MCP сервер доступен всему миру 🎉
