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
|TELEGRAM_GROUP |❌| ChatId del grupo. Si este bot va a formar parte de un grupo, es necesario especificar el chatId de dicho grupo. El bot debe ser administrador del grupo |
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
Para su ejecución en local y probar nuevos cambios de código, el repositorio ya incluye `Dockerfile_local` y `docker-compose.yaml`. Solo necesitas crear un fichero `.env` con tu configuración.

La estructura de carpetas es la del propio repositorio (todo en la raíz):
```
wakebot/
├── Dockerfile_local
├── docker-compose.yaml
├── .dockerignore
├── .env-example
├── .env
├── requirements.txt
├── config.py
├── wakebot.py
├── device_store.py
└── locale
    ├── en.json
    └── es.json
```

El fichero `.env` contiene los datos sensibles (token, chatId...) y está ignorado por git, por lo que **no se sube al repositorio**. Como plantilla se proporciona un `.env-example` que puedes copiar:
```
cp .env-example .env
```
Después edita `.env` y rellena tus valores reales.

.env-example
```
# OBLIGATORIO - Token del bot de Telegram (obtenido de @BotFather)
TELEGRAM_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTuVwXyZ

# OBLIGATORIO - ChatId del administrador (varios separados por comas: 12345,54431)
TELEGRAM_ADMIN=12345678

# OBLIGATORIO - Timezone (por ejemplo Europe/Madrid)
TZ=Europe/Madrid

# OPCIONAL - ChatId del grupo (si el bot forma parte de un grupo)
#TELEGRAM_GROUP=-1001234567890

# OPCIONAL - Thread del tema dentro de un supergrupo (valor numérico). Por defecto 1
#TELEGRAM_THREAD=1

# OPCIONAL - Idioma: ES / EN. Por defecto ES
#LANGUAGE=ES
```

Dockerfile_local
```
FROM alpine:3.24.1

WORKDIR /app

RUN apk add --no-cache python3 py3-pip tzdata

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "wakebot.py"]
```

docker-compose.yaml
```yaml
services:
    test-wakebot:
        container_name: test-wakebot
        environment:
            - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
            - TELEGRAM_ADMIN=${TELEGRAM_ADMIN}
            - TZ=${TZ:-Europe/Madrid}
            #- TELEGRAM_GROUP=${TELEGRAM_GROUP}
            #- TELEGRAM_THREAD=${TELEGRAM_THREAD:-1}
            #- LANGUAGE=${LANGUAGE:-ES}
        volumes:
            - ./data:/app/data
        build:
          context: .
          dockerfile: ./Dockerfile_local
        restart: always
        network_mode: host
        tty: true
```

Los valores `${...}` se leen automáticamente del fichero `.env` que se encuentra junto al `docker-compose.yaml`. Es necesario establecer un `TELEGRAM_TOKEN` y un `TELEGRAM_ADMIN` correctos y diferentes al de la ejecución normal. Los datos de los dispositivos se guardan en la carpeta `./data`, ignorada por git. El `.dockerignore` evita que el `.env` y otros ficheros sensibles entren en la imagen.

Para levantarlo habría que ejecutar en la raíz del repositorio: `docker compose up -d`

Para detenerlo y probar nuevos cambios habría que ejecutar en esa ruta: `docker compose down --rmi`
