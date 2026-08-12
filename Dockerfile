FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Версия poetry закреплена. Было просто "pip install poetry": образ собирался
# тем, что окажется свежим на момент сборки, и смена мажорной версии могла
# сломать сборку молча - формат pyproject и lock-файла между 1.x и 2.x разный.
# --without dev: pytest нужен только для тестов, в образе ему делать нечего.
RUN pip install --no-cache-dir "poetry==2.4.1" \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --without dev --no-interaction --no-ansi

COPY . .

# Без --reload: перезагрузчик нужен при разработке, и он включается командой
# в docker-compose. Умолчание образа должно быть боевым.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
