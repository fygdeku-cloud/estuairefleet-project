set dotenv-load := true

install:
    uv sync

run:
    uv run python manage.py runserver

check:
    uv run python manage.py check
    uv run ruff check .

test:
    uv run pytest

format:
    uv run ruff format .

migrations:
    uv run python manage.py makemigrations
    uv run python manage.py migrate

local:
    docker compose -f docker-compose.local.yml up --build
