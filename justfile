set dotenv-load := true

install:
    uv sync

up:
    docker compose -f docker-compose.local.yml up --build

down:
    docker compose -f docker-compose.local.yml down

run:
    uv run python manage.py runserver

test:
    uv run pytest

lint:
    uv run ruff check .
    uv run ruff format --check .

fmt:
    uv run ruff format .

migrate:
    uv run python manage.py migrate

makemigrations:
    uv run python manage.py makemigrations

seed:
    uv run python manage.py seed_demo

css:
    npm run build:css

verify:
    uv run ruff check .
    uv run ruff format --check .
    uv run python manage.py makemigrations --check --dry-run
    uv run python manage.py check
    uv run pytest
    npm run build:css

shell:
    uv run python manage.py shell

logs:
    docker compose -f docker-compose.local.yml logs -f django

screenshots:
    uv run python tests/visual/screenshots.py
