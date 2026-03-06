ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG C.UTF-8

RUN apk add --no-cache \
    bash \
    curl \
    jq

WORKDIR /app

COPY app /app/app
COPY run.sh /run.sh

RUN chmod a+x /run.sh

RUN pip install --no-cache-dir \
    flask==3.0.3 \
    requests==2.32.3 \
    waitress==3.0.0

CMD [ "/run.sh" ]
