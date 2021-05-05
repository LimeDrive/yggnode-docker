FROM python:3.9-slim-buster

WORKDIR /yggnode

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
