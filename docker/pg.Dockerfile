FROM postgres:14.1
COPY ./setup_db.sh /docker-entrypoint-initdb.d