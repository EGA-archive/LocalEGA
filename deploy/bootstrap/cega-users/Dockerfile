##########################
## Build env
##########################
FROM python:3.9-alpine as BUILD

RUN apk add gcc musl-dev

RUN pip install --upgrade pip && \
    pip install aiohttp

##########################
## Final image
##########################
FROM python:3.9-alpine

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"

COPY --from=BUILD usr/local/lib/python3.9/ usr/local/lib/python3.9/

VOLUME /cega/users

COPY server.py /cega/server.py

ENTRYPOINT ["python", "/cega/server.py", "0.0.0.0", "443", "/cega/users"]
