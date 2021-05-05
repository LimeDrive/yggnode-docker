FROM python:3.9-slim-buster

WORKDIR /yggnode-resync

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
# COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt

RUN pip3 install flask torrentool

COPY . .

CMD [ "python", "resync.py" ]
