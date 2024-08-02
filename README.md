# wakebot
[![](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/dgongut/wakebot)
[![](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/dgongut/wakebot)
[![](https://badgen.net/badge/icon/telegram?icon=telegram&label)](https://t.me/dockercontrollerbotnews)
[![Docker Pulls](https://badgen.net/docker/pulls/dgongut/wakebot?icon=docker&label=pulls)](https://hub.docker.com/r/dgongut/wakebot/)
[![Docker Stars](https://badgen.net/docker/stars/dgongut/wakebot?icon=docker&label=stars)](https://hub.docker.com/r/dgongut/wakebot/)
[![Docker Image Size](https://badgen.net/docker/size/dgongut/wakebot?icon=docker&label=image%20size)](https://hub.docker.com/r/dgongut/wakebot/)
![Github stars](https://badgen.net/github/stars/dgongut/wakebot?icon=github&label=stars)
![Github forks](https://badgen.net/github/forks/dgongut/wakebot?icon=github&label=forks)
![Github last-commit](https://img.shields.io/github/last-commit/dgongut/wakebot)
![Github last-commit](https://badgen.net/github/license/dgongut/wakebot)
![alt text](https://github.com/dgongut/pictures/blob/main/WakeBot/mockup.png)

Despierta mediante Wake on LAN dispositivos en tu red

¿Lo buscas en [![](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/dgongut/wakebot)?

🖼️ Si deseas establecerle el icono al bot de telegram, te dejo [aquí](https://raw.githubusercontent.com/dgongut/pictures/main/WakeBot/WakeBot.png) el icono en alta resolución. Solo tienes que descargarlo y mandárselo al @BotFather en la opción de BotPic.

## Configuración en config.py

| CLAVE  | OBLIGATORIO | VALOR |
|:------------- |:---------------:| :-------------|
|TELEGRAM_TOKEN |✅| Token del bot |
|TELEGRAM_ADMIN |✅| ChatId del administrador (se puede obtener hablándole al bot Rose escribiendo /id). Admite múltiples administradores separados por comas. Por ejemplo 12345,54431,55944 |
|TELEGRAM_GROUP |❌| ChatId del grupo. Si este bot va a formar parte de un grupo, es necesario especificar el chatId de dicho grupo |
|TELEGRAM_THREAD |❌| Thread del tema dentro de un supergrupo; valor numérico (2,3,4..). Por defecto 1. Se utiliza en conjunción con la variable TELEGRAM_GROUP |
|TZ |✅| Timezone (Por ejemplo Europe/Madrid) |
|LANGUAGE |❌| Idioma, puede ser ES / EN. Por defecto es ES (Spanish) | 

### Anotaciones
Será necesario mapear un volumen para almacenar lo que el bot escribe en /app/data

### Ejemplo de Docker-Compose para su ejecución normal
```yaml
version: '3.3'
services:
    wakebot:
        environment:
            - TELEGRAM_TOKEN=
            - TELEGRAM_ADMIN=
            - TZ=Europe/Madrid
            #- TELEGRAM_GROUP=
            #- TELEGRAM_THREAD=1
            #- LANGUAGE=ES
        volumes:
            - /ruta/para/guardar/las/programaciones:/app/data # CAMBIAR LA PARTE IZQUIERDA
        image: dgongut/wakebot:latest
        container_name: wakebot
        restart: always
        network_mode: host
        tty: true
```

---

## Solo para desarrolladores - Ejecución con código local
Para su ejecución en local y probar nuevos cambios de código, se necesitan crear 2 ficheros llamados respectivamente Dockerfile_local y docker-compose.yaml

La estructura de carpetas debe quedar:
```
wakebot/
├── Dockerfile_local
├── docker-compose.yaml
└── src
    ├── LICENSE
    ├── README.md
    ├── config.py
    ├── wakebot.py
    └── locale
        ├── en.json
        └── es.json
```

Dockerfile_local
```
FROM alpine:3.18.6

ENV TELEGRAM_TOKEN abc
ENV TELEGRAM_ADMIN abc
ENV TELEGRAM_GROUP abc
ENV TELEGRAM_THREAD 1
ENV LANGUAGE ES
ENV TZ UTC

RUN apk add --no-cache python3 py3-pip tzdata
RUN pip3 install pyTelegramBotAPI==4.17.0
RUN pip3 install wakeonlan==3.1.0

WORKDIR /app
COPY src/ .

ENTRYPOINT ["python3", "wakebot.py"]
```

docker-compose.yaml
```yaml
version: '3.3'
services:
    TEST-wakebot:
        container_name: TEST-wakebot
        environment:
            - TELEGRAM_TOKEN=
            - TELEGRAM_ADMIN=
            - TZ=Europe/Madrid
            #- TELEGRAM_GROUP=
            #- TELEGRAM_THREAD=1
            #- LANGUAGE=ES
        volumes:
            - /ruta/para/guardar/las/programaciones:/app/data # CAMBIAR LA PARTE IZQUIERDA
        build:
          context: .
          dockerfile: ./Dockerfile_local
        tty: true
```

Es necesario establecer un `TELEGRAM_TOKEN` y un `TELEGRAM_ADMIN` correctos y diferentes al de la ejecución normal.

Para levantarlo habría que ejecutar en esa ruta: `docker compose up -d`

Para detenerlo y probar nuevos cambios habría que ejecutar en esa ruta: `docker compose down --rmi`
