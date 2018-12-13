FROM python:3.7-alpine
LABEL maintainer "EGA System Developers"

RUN apk add --no-cache \
    libressl libressl-dev make gcc musl-dev libffi-dev postgresql-libs postgresql-dev git

#################################################
##
## Install LocalEGA stuff
##
#################################################

RUN addgroup lega && \
    adduser -D -G lega lega

# RUN git clone https://github.com/EGA-archive/crypt4gh.git /root/crypt4gh && \
#     pip3.6 install -r /root/crypt4gh/requirements.txt && \
#     rm -rf /root/crypt4gh

ARG checkout=master
RUN git clone https://github.com/EGA-archive/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout}

RUN pip install -r /root/LocalEGA/requirements.txt && \
    pip install /root/LocalEGA && \
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
