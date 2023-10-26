##########################
## Build env
##########################
FROM python:3.11-slim as BUILD

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    	    gcc make bzip2 libpq5 libpq-dev libffi-dev libssl-dev libc-dev-bin libc-dev

# This will pin the package versions
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


##########################
## Final image
##########################
FROM python:3.11-slim

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="2.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"

COPY --from=BUILD /usr/local/lib/            /usr/local/lib/
#COPY --from=BUILD /usr/local/lib/python3.11/ /usr/local/lib/python3.11/

# The running user inside the container should not be root
# Since the user will create files, it is convenient to make that
# user the same as the calling user building/using the docker container.
# At the build stage, pass 2 --build-arg arguments and make them match
# the running user, with for example LEGA_UID=$(id -u) and LEGA_GID=$(id -g)
ARG LEGA_UID=1000
ARG LEGA_GID=1000

RUN ldconfig -v                            && \
    groupadd -g ${LEGA_GID} -r lega        && \
    useradd -M -g lega -u ${LEGA_UID} lega && \
    mkdir -p /ega/staging                  && \
    mkdir -p /ega/vault                    && \
    mkdir -p /ega/vault.bkp                && \
    mkdir -p /etc/ega                      && \
    chgrp lega /ega/staging                && \
    chgrp lega /ega/vault                  && \
    chgrp lega /ega/vault.bkp              && \
    chgrp lega /etc/ega                    && \
    chmod 2770 /ega/staging                && \
    chmod 2770 /ega/vault                  && \
    chmod 2770 /ega/vault.bkp              && \
    chmod 2770 /etc/ega

VOLUME /ega/vault
VOLUME /ega/vault.bkp
VOLUME /ega/staging
VOLUME /etc/ega

COPY code /ega/code

USER lega
WORKDIR /ega
ENTRYPOINT ["python", "-m", "code"]
#CMD ["/etc/ega/lega.ini"] # injected config file
