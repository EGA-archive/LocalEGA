##########################
## Build env
##########################
FROM python:3.11-slim as BUILD

RUN pip install --upgrade pip && \
    pip install aiohttp aiormq


##########################
## Final image
##########################
FROM python:3.11-slim

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="2.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"

COPY --from=BUILD /usr/local/lib/python3.11/ /usr/local/lib/python3.11/

RUN groupadd ega && \
    useradd -M -g ega ega && \
    mkdir /ega

COPY server.py /ega/server.py
COPY users/users.json /ega/users.json

USER ega
WORKDIR /ega
ENTRYPOINT ["python", "server.py"]
