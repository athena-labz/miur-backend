FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

WORKDIR /app

COPY ./src/nginx.conf /etc/nginx/conf.d