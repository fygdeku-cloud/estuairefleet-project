FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv pip install --system . django-debug-toolbar django-extensions
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
