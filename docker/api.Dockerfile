FROM tiangolo/uwsgi-nginx:python3.9

RUN apt-get update && apt-get install -y 
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./src/uwsgi.ini ./uwsgi.ini
WORKDIR /app/src