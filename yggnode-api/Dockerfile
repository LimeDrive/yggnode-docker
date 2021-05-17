FROM python:3.9-slim-buster

WORKDIR /yggnode-api
ENV TZ=Europe/Paris

RUN mkdir --parents blackhole/{torrents,rss}/tmp config/
RUN pip install --upgrade pip && pip install flask PyYAML torrentool gunicorn gevent

COPY . .

EXPOSE 5000

ENTRYPOINT [ "gunicorn" ]
CMD [ "__init__:app", "-b", "0.0.0.0:5000", "--worker-class=gevent", "--worker-connections=250", "--workers=3"]