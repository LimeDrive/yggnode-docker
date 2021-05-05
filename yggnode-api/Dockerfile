FROM python:3.9-slim-buster

WORKDIR /yggnode-api

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD [ "python", "yggnode.py" ]