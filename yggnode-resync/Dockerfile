FROM python:3.9-slim-buster

WORKDIR /yggnode-resync

ENV TZ=Europe/Paris

RUN mkdir --parents blackhole/{torrents,rss}/tmp config/
RUN pip install --upgrade pip && pip install requests PyYAML torrentool

COPY . .

CMD [ "python", "resync.py" ]
