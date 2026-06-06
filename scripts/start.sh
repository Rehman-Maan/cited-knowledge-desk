#!/bin/sh
set -eu

if [ "${RENDER_FREE_DEPLOYMENT:-False}" = "True" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py seed_public_demo
fi

exec daphne -b 0.0.0.0 -p "${PORT:-8000}" config.asgi:application
