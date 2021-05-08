FROM python:3.9-slim-buster

WORKDIR /yggnode-api
ENV TZ=Europe/Paris

RUN mkdir --parents blackhole/{torrents,rss}/tmp config/
RUN pip install --upgrade pip && pip install flask PyYAML torrentool

COPY . .

EXPOSE 5000

CMD [ "yggnode.py" ]
ENTRYPOINT [ "python3" ]