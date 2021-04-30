##########################
## Build env, it works with debian buster 3.8
##########################
FROM python:3.9-slim as BUILD

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    		gcc make bzip2 \
		libpq5 libpq-dev libffi-dev libssl-dev libc-dev-bin libc-dev \
	&& rm -rf /var/lib/apt/lists/*

# This will pin the package versions
COPY requirements.txt /root/LocalEGA/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /root/LocalEGA/requirements.txt

COPY setup.py /root/LocalEGA/setup.py
COPY lega /root/LocalEGA/lega
RUN pip install /root/LocalEGA


##########################
## Final image
##########################
FROM python:3.9-slim

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"


ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
		libpq5 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=BUILD usr/local/lib/python3.9/ usr/local/lib/python3.9/
COPY --from=BUILD /usr/local/bin/ega-* /usr/local/bin/

ARG LEGA_UID=1000
ARG LEGA_GID=1000
ARG LEGA_USERNAME=lega
ARG LEGA_GROUPNAME=lega

RUN ldconfig -v                                  && \
    groupadd -g ${LEGA_GID} -r ${LEGA_GROUPNAME} && \
    useradd -M -g ${LEGA_GROUPNAME} -u ${LEGA_UID} ${LEGA_USERNAME} && \
    mkdir -p /ega/staging                        && \
    chgrp ${LEGA_USERNAME} /ega/staging          && \
    chmod 2770 /ega/staging                      && \
    mkdir -p /ega/vault                          && \
    chgrp ${LEGA_USERNAME} /ega/vault            && \
    chmod 2770 /ega/vault                        && \
    mkdir -p /ega/vault.bkp                      && \
    chgrp ${LEGA_USERNAME} /ega/vault.bkp        && \
    chmod 2770 /ega/vault.bkp                    && \
    mkdir -p /etc/ega                            && \
    chgrp ${LEGA_USERNAME} /etc/ega              && \
    chmod 2770 /etc/ega

VOLUME /ega/vault
VOLUME /ega/vault.bkp
VOLUME /ega/staging
VOLUME /etc/ega

USER ${LEGA_USERNAME}

