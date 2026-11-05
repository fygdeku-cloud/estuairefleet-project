FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN pip install --no-cache-dir uv
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv pip install --system . django-debug-toolbar django-extensions pytest pytest-django ruff
COPY . .
USER app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
