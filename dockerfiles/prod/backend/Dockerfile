FROM python:3.12-slim AS builder

WORKDIR /usr/src/web

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# --------- stage2 ---------

FROM python:3.12-slim

RUN useradd -m -r django-user && \
    mkdir -p /usr/src/web/staticfiles && \
    chown -R django-user /usr/src/web

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

    
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/


WORKDIR /usr/src/web

USER django-user

COPY --chown=django-user:django-user --chmod=755 ./dockerfiles/prod/backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

COPY --chown=django-user:django-user ./backend/manage.py .
COPY --chown=django-user:django-user ./backend/project ./project


COPY --chown=django-user:django-user ./backend/apps ./apps

ENTRYPOINT [ "./entrypoint.sh" ]