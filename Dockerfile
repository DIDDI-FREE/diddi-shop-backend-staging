FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app_base ./app_base
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN python -m pip install --upgrade pip \
    && python -m pip uninstall -y jwt \
    && python -m pip install . \
    && python -c "import jwt; from jwt import PyJWK; assert jwt.__version__.split('.')[0] == '2'; assert PyJWK"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app_base.main:app", "--host", "0.0.0.0", "--port", "8000"]
