FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Спочатку залежності — щоб Docker кешував цей шар
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Запуск не від root
RUN useradd --create-home appuser
USER appuser

# Версія застосунку передається під час збірки:
#   docker build --build-arg APP_VERSION=1.0.0 -t tasks-api:1.0.0 ./api
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
LABEL org.opencontainers.image.version=${APP_VERSION}

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]
