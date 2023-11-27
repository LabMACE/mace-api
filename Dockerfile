FROM python:3.11.6-alpine3.18
ENV POETRY_VERSION=1.6.1
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/
RUN poetry config installer.max-workers 10
RUN poetry config virtualenvs.create false
RUN apk add --no-cache g++ geos-dev
RUN poetry install --no-interaction --without dev

COPY alembic.ini prestart.sh /app
COPY migrations /app/migrations
COPY app /app/app

ENTRYPOINT sh prestart.sh
