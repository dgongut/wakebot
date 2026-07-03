FROM alpine:3.24.1

ARG VERSION=1.1.0

WORKDIR /app

RUN apk add --no-cache python3 py3-pip tzdata && \
    wget -q "https://github.com/dgongut/wakebot/archive/refs/tags/v${VERSION}.tar.gz" -O /tmp/wakebot.tar.gz && \
    tar -xf /tmp/wakebot.tar.gz -C /tmp && \
    cp /tmp/wakebot-${VERSION}/wakebot.py /tmp/wakebot-${VERSION}/config.py /tmp/wakebot-${VERSION}/device_store.py /tmp/wakebot-${VERSION}/requirements.txt /app/ && \
    cp -r /tmp/wakebot-${VERSION}/locale /app/locale && \
    rm -rf /tmp/wakebot.tar.gz /tmp/wakebot-${VERSION} && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt

ENTRYPOINT ["python3", "wakebot.py"]
