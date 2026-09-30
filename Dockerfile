FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: this layer is rebuilt only when requirements change.
COPY requirements/base.txt requirements/base.txt
RUN pip install -r requirements/base.txt

COPY . .

# Collect static files at build time (values below are placeholders used only for this step).
RUN DJANGO_SECRET_KEY=build-only \
    DATABASE_URL=sqlite:////tmp/build.db \
    DJANGO_ALLOWED_HOSTS=build.local \
    DJANGO_CSRF_TRUSTED_ORIGINS=https://build.local \
    DJANGO_ADMIN_URL=build-only/ \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    python manage.py collectstatic --noinput

# Never run as root.
RUN useradd --system --no-create-home --uid 10001 app
USER app

ENV DJANGO_SETTINGS_MODULE=config.settings.prod
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]