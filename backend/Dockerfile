FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV DJANGO_DEBUG=0

EXPOSE 8000

CMD python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn breathe_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}
