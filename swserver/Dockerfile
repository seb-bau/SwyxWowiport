FROM python:3.11-slim-bookworm

RUN mkdir /app
WORKDIR /app

RUN set -e; \
        apt-get update; \
        apt-get install -y \
                build-essential \
        ;

EXPOSE 5000
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "uwsgi", "--ini", "app.ini" ]