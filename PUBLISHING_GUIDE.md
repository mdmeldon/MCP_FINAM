# 📦 Руководство по публикации MCP сервера на PyPI

Это пошаговое руководство объясняет, как опубликовать ваш MCP сервер на PyPI, чтобы пользователи могли запускать его через `uvx`.

## 📋 Предварительные требования

### 1. Установленные инструменты

```bash
# Установите uv (если еще не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установите build и twine для публикации
uv pip install build twine
```

### 2. Аккаунт на PyPI

1. Зарегистрируйтесь на [PyPI](https://pypi.org/account/register/)
2. Подтвердите email
3. Настройте 2FA (двухфакторную аутентификацию) - это обязательно для публикации

### 3. Создайте API токен на PyPI

1. Перейдите в [настройки API токенов](https://pypi.org/manage/account/token/)
2. Нажмите "Add API token"
3. Введите имя токена (например, "finam-mcp-publishing")
4. Для первой публикации выберите "Scope: Entire account (all projects)"
5. Нажмите "Add token"
6. **ВАЖНО:** Скопируйте токен сразу! Он показывается только один раз
7. Токен выглядит так: `pypi-AgEIcHlwaS5vcmc...`

## 🔧 Подготовка проекта

### 1. Обновите метаданные в `pyproject.toml`

Откройте `pyproject.toml` и обновите следующие поля:

```toml
[project]
name = "finam-mcp"  # Имя должно быть уникальным на PyPI
version = "0.1.0"   # Следуйте семантическому версионированию
description = "Ваше описание"
authors = [
    {name = "Ваше имя", email = "ваш.email@example.com"}
]

[project.urls]
Homepage = "https://github.com/ваш-username/finam-mcp"
Repository = "https://github.com/ваш-username/finam-mcp"
Issues = "https://github.com/ваш-username/finam-mcp/issues"
```

### 2. Проверьте структуру проекта

Убедитесь, что структура выглядит так:

```
finam-mcp/
├── finam_mcp/           # Пакет Python
│   ├── __init__.py
│   └── server.py
├── pyproject.toml       # Конфигурация проекта
├── README.md           # Документация
├── LICENSE             # Лицензия
├── MANIFEST.in         # Дополнительные файлы для включения
└── .gitignore          # Игнорируемые файлы
```

### 3. Проверьте, что имя пакета свободно

```bash
# Поиск на PyPI
pip search finam-mcp
# Или проверьте на https://pypi.org/project/finam-mcp/
```

Если имя занято, выберите другое (например, `finam-mcp-server`, `mcp-finam` и т.д.).

## 🏗️ Сборка пакета

### 1. Очистите предыдущие сборки (если есть)

```bash
cd /Users/graph/services/Pet_projects/mcp/Finam
rm -rf dist/ build/ *.egg-info finam_mcp.egg-info
```

### 2. Соберите пакет

```bash
# Сборка дистрибутива
python -m build

# Или через uv
uv build
```

После успешной сборки в директории `dist/` появятся два файла:

- `finam_mcp-0.1.0-py3-none-any.whl` (wheel файл)
- `finam_mcp-0.1.0.tar.gz` (source distribution)

### 3. Проверьте содержимое пакета

```bash
# Проверьте wheel файл
unzip -l dist/finam_mcp-0.1.0-py3-none-any.whl

# Проверьте tar.gz
tar -tzf dist/finam_mcp-0.1.0.tar.gz
```

## 🧪 Тестирование перед публикацией

### 1. Проверьте пакет локально

```bash
# Установите собранный пакет локально
uv pip install dist/finam_mcp-0.1.0-py3-none-any.whl

# Попробуйте запустить
finam-mcp --help

# Или напрямую
python -c "from finam_mcp import main; main()"
```

### 2. Проверьте через twine

```bash
twine check dist/*
```

Эта команда проверит, что ваш пакет соответствует требованиям PyPI.

### 3. (Опционально) Публикация на TestPyPI

TestPyPI - это тестовая версия PyPI для проверки публикации:

```bash
# Загрузите на TestPyPI
twine upload --repository testpypi dist/*

# Введите:
# Username: __token__
# Password: <ваш TestPyPI токен>

# Протестируйте установку с TestPyPI
pip install --index-url https://test.pypi.org/simple/ finam-mcp

# Протестируйте через uvx
uvx --index-url https://test.pypi.org/simple/ finam-mcp
```

Для TestPyPI создайте отдельный токен на [test.pypi.org](https://test.pypi.org/).

## 🚀 Публикация на PyPI

### Способ 1: Через twine (рекомендуется)

```bash
# Загрузите на PyPI
twine upload dist/*

# Введите учетные данные:
# Username: __token__
# Password: <ваш PyPI токен, начинается с pypi-...>
```

### Способ 2: Через uv

```bash
# С uv 0.4.0+ можно публиковать напрямую
uv publish

# Или с явным указанием токена
uv publish --token <ваш_токен>
```

### Способ 3: Настройка ~/.pypirc для автоматизации

Создайте файл `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEI...
```

**ВАЖНО:** Установите правильные права доступа:

```bash
chmod 600 ~/.pypirc
```

Теперь можно публиковать без ввода пароля:

```bash
twine upload dist/*
```

## ✅ Проверка публикации

### 1. Проверьте на PyPI

Откройте в браузере: `https://pypi.org/project/finam-mcp/`

### 2. Протестируйте установку

```bash
# Обычная установка
pip install finam-mcp

# Через uvx (это то, что нужно!)
uvx finam-mcp
```

### 3. Проверьте в конфигурации MCP

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "finam": {
      "command": "uvx",
      "args": ["finam-mcp"],
      "env": {
        "TEST_ENV": "test_value"
      }
    }
  }
}
```

Перезапустите Claude Desktop/Cursor и проверьте, что сервер доступен.

## 🔄 Обновление пакета

Когда нужно выпустить новую версию:

### 1. Обновите версию

В `pyproject.toml`:

```toml
[project]
version = "0.1.1"  # Увеличьте версию
```

Следуйте [семантическому версионированию](https://semver.org/):

- `0.1.0` → `0.1.1` - исправления багов (patch)
- `0.1.0` → `0.2.0` - новые функции (minor)
- `0.1.0` → `1.0.0` - несовместимые изменения (major)

### 2. Обновите CHANGELOG (рекомендуется)

Создайте `CHANGELOG.md` и описывайте изменения:

```markdown
## [0.1.1] - 2025-10-03

### Fixed

- Исправлена ошибка в обработке...

### Added

- Добавлена новая функция...
```

### 3. Пересоберите и опубликуйте

```bash
# Очистите старые сборки
rm -rf dist/

# Соберите новую версию
python -m build

# Опубликуйте
twine upload dist/*
```

### 4. Создайте тег в Git (рекомендуется)

```bash
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

## 📚 Дополнительные рекомендации

### 1. Используйте GitHub Actions для автоматической публикации

Создайте `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

Добавьте ваш PyPI токен в GitHub Secrets.

### 2. Добавьте бейджи в README

```markdown
[![PyPI version](https://badge.fury.io/py/finam-mcp.svg)](https://badge.fury.io/py/finam-mcp)
[![Downloads](https://pepy.tech/badge/finam-mcp)](https://pepy.tech/project/finam-mcp)
```

### 3. Напишите хорошую документацию

- Подробный README с примерами
- Документация API
- Примеры использования
- FAQ

## 🐛 Решение проблем

### Ошибка: "Package already exists"

Нельзя повторно загрузить ту же версию. Увеличьте версию в `pyproject.toml`.

### Ошибка: "Invalid credentials"

- Проверьте токен (должен начинаться с `pypi-`)
- Убедитесь, что используете `__token__` как username
- Проверьте, что токен не истек

### Ошибка: "Package name already taken"

Выберите другое имя пакета в `pyproject.toml`.

### uvx не находит пакет

- Подождите 1-2 минуты после публикации (индекс PyPI обновляется)
- Проверьте имя пакета: `uvx finam-mcp` (используйте точное имя из PyPI)
- Убедитесь, что в пакете есть `[project.scripts]` в `pyproject.toml`

## 📞 Полезные ссылки

- [PyPI](https://pypi.org/)
- [Документация packaging.python.org](https://packaging.python.org/)
- [Документация Twine](https://twine.readthedocs.io/)
- [uv документация](https://docs.astral.sh/uv/)
- [Семантическое версионирование](https://semver.org/)

---

Готово! Ваш MCP сервер теперь доступен всему миру через `uvx finam-mcp` 🎉
