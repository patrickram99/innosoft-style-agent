FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/innosoft

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY rules ./rules
COPY prompts ./prompts
COPY alembic ./alembic
COPY alembic.ini .

RUN mkdir -p storage

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
