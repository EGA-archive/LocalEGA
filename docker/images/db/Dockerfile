FROM postgres:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN  apt-get update \
  && apt-get install -y wget ca-certificates python-pip python-dev build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Setup
RUN gpg --list-keys && \
    gpg --keyserver pgp.mit.edu --recv-keys 0x698F1519
# Maintainer: Dave Page <dpage@pgadmin.org>

##################################
# For PgAdmin4
##################################

ARG PGADMIN4_VERSION=1.6

RUN mkdir -p /var/src/pgadmin4
WORKDIR /var/src/pgadmin4

RUN wget -c https://ftp.postgresql.org/pub/pgadmin/pgadmin4/v${PGADMIN4_VERSION}/pip/pgadmin4-${PGADMIN4_VERSION}-py2.py3-none-any.whl && \
    wget -c https://ftp.postgresql.org/pub/pgadmin/pgadmin4/v${PGADMIN4_VERSION}/pip/pgadmin4-${PGADMIN4_VERSION}-py2.py3-none-any.whl.sig && \
    gpg --verify pgadmin4-${PGADMIN4_VERSION}-py2.py3-none-any.whl.sig

RUN pip install --upgrade pip 
RUN pip install ./pgadmin4-${PGADMIN4_VERSION}-py2.py3-none-any.whl

##################################
RUN rm -rf /var/src/pgadmin4
WORKDIR /

##################################
COPY db.sql /docker-entrypoint-initdb.d/db.sql

##################################
# Configuring

EXPOSE 5050

RUN mkdir -p /var/{log,lib}/pgadmin4/
COPY config_local.py /usr/local/lib/python2.7/dist-packages/pgadmin4/config_local.py
COPY requirements.txt /usr/local/lib/python2.7/dist-packages/pgadmin4/requirements.txt

RUN pip install uwsgi virtualenv virtualenvwrapper

RUN echo 'source /usr/local/bin/virtualenvwrapper.sh' >> /root/.bashrc

RUN rm /bin/sh && ln -s /bin/bash /bin/sh
RUN source /usr/local/bin/virtualenvwrapper.sh && \
    mkvirtualenv pgadmin4 && \
    workon pgadmin4 && \
    pip install -r /usr/local/lib/python2.7/dist-packages/pgadmin4/requirements.txt
