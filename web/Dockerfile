# syntax=docker/dockerfile:1

FROM python:3.12.2-slim-bullseye

EXPOSE 80

WORKDIR /flask_blog

ENV FLASK_APP=/flask_blog/SiteFiles/wsgi.py

COPY files/requirements.txt /flask_blog/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y python3-dev build-essential libpcre3 libpcre3-dev

RUN pip3 install --no-cache wheel flask pymongo virtualenv pandas hvac

RUN pip3 install uwsgi

COPY files /flask_blog/

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=80"]
