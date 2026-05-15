FROM python:3.12-slim

WORKDIR /usr/src/web

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/


COPY ./requirements.txt .
RUN pip install -r requirements.txt