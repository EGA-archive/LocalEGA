FROM python:3.6-alpine3.8
LABEL maintainer "EGA System Developers"

RUN apk add --no-cache \
    libressl libressl-dev make gcc musl-dev libffi-dev postgresql-libs postgresql-dev git
RUN pip install --upgrade pip

#################################################
##
## Install LocalEGA stuff
##
#################################################

ARG LEGA_GID=1000
RUN addgroup -g ${LEGA_GID} lega && \
    adduser -D -G lega lega

COPY setup.py /root/LocalEGA/setup.py
COPY lega /root/LocalEGA/lega
COPY requirements.txt /root/LocalEGA/requirements.txt

RUN pip install -r /root/LocalEGA/requirements.txt
RUN pip install /root/LocalEGA && \
    rm -rf /root/LocalEGA

RUN apk del --no-cache --purge \
            gcc git make \
	    postgresql-dev musl-dev libffi-dev libressl-dev \
    && rm -rf /var/cache/apk/*

# Replaces the need for gosu
# But instead, we use the 'user:' in the docker-compose file
# to still leave the door open for debugging
#
# USER lega
