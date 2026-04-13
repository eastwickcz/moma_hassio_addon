ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

COPY app /app
COPY run.sh /run.sh

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
