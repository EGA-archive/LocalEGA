#!/usr/bin/env bash

mkdir -p $PRIVATE/lega/{pgp,certs,logs}
chmod 700 $PRIVATE/lega/{pgp,certs,logs}

echomsg "\t* the PGP key"

# Running in a container
GEN_KEY="python3.6 /tmp/generate_pgp_key.py"

# Python 3.6
${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/lega/pgp/ega.pub --priv ${PRIVATE}/lega/pgp/ega.sec --armor
chmod 644 ${PRIVATE}/lega/pgp/ega.pub

${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/lega/pgp/ega2.pub --priv ${PRIVATE}/lega/pgp/ega2.sec --armor
chmod 644 ${PRIVATE}/lega/pgp/ega2.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/lega/certs/ssl.key -nodes -out ${PRIVATE}/lega/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.ini"
${OPENSSL} enc -aes-256-cbc -salt -out ${PRIVATE}/lega/keys.ini.enc -md md5 -k ${KEYS_PASSWORD} <<EOF
[DEFAULT]
active : key.1

[key.1]
path : /etc/ega/pgp/ega.sec
passphrase : ${PGP_PASSPHRASE}
expire: 30/MAR/19 08:00:00

[key.2]
path : /etc/ega/pgp/ega2.sec
passphrase : ${PGP_PASSPHRASE}
expire: 30/MAR/18 08:00:00
EOF


echomsg "\t* conf.ini"
cat > ${PRIVATE}/lega/conf.ini <<EOF
[DEFAULT]
log = debug
#log = silent

[keyserver]
port = 8443

[quality_control]
keyserver_endpoint = https://keys:8443/retrieve/%s/private

[inbox]
location = /ega/inbox/%s
chroot_sessions = True

[vault]
driver = S3Storage
url = http://s3:9000
access_key = ${S3_ACCESS_KEY}
secret_key = ${S3_SECRET_KEY}
#region = lega


[outgestion]
# Just for test
keyserver_endpoint = https://keys:8443/retrieve/%s/private

## Connecting to Local EGA
[broker]
host = mq
connection_attempts = 30
# delay in seconds
retry_delay = 10

[postgres]
host = db
user = ${DB_USER}
password = ${DB_PASSWORD}
try = 30

[eureka]
endpoint = http://cega-eureka:8761
EOF


#########################################################################
# Populate env-settings for docker compose
#########################################################################

# For the moment, still using guest:guest
echomsg "\t* Local broker to Central EGA broker credentials"
cat > ${PRIVATE}/lega/mq.env <<EOF
CEGA_CONNECTION=amqp://lega:${CEGA_MQ_PASSWORD}@cega-mq:5672/lega
EOF

#########################################################################
# Creating the docker-compose file
#########################################################################
cat >> ${PRIVATE}/lega.yml <<EOF
version: '3.2'

networks:
  lega:
    # user overlay in swarm mode
    # default is bridge
    driver: bridge
  cega:
    external: true

services:

  ############################################
  # Local EGA instance
  ############################################

  # Local Message broker
  mq:
    env_file: lega/mq.env
    hostname: mq
    ports:
      - "${DOCKER_PORT_mq}:15672"
    image: rabbitmq:3.6.14-management
    container_name: mq
    restart: on-failure:3
    # Required external link
    external_links:
      - cega-mq:cega-mq
    networks:
      - lega
      - cega
    volumes:
      - ../images/mq/defs.json:/etc/rabbitmq/defs.json
      - ../images/mq/rabbitmq.config:/etc/rabbitmq/rabbitmq.config
      - ../images/mq/entrypoint.sh:/usr/bin/ega-entrypoint.sh
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]
    command: ["rabbitmq-server"]

  # Postgres Database
  db:
    environment:
      - DB_INSTANCE=db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=lega
      - PGDATA=/ega/data
    hostname: db
    container_name: db
    image: postgres:9.6
    volumes:
      - db:/ega/data
      - ../images/db/db.sql:/docker-entrypoint-initdb.d/ega.sql:ro
    restart: on-failure:3
    networks:
      - lega

  # SFTP inbox
  inbox:
    hostname: ega-inbox
    depends_on:
      - mq
    # Required external link
    external_links:
      - cega-users:cega-users
    container_name: inbox
    restart: on-failure:3
    networks:
      - lega
      - cega
EOF
if [[ $INBOX == 'mina' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
    environment:
      - CEGA_ENDPOINT=http://cega-users/user/
      - CEGA_ENDPOINT_CREDS=lega:${CEGA_REST_PASSWORD}
    ports:
      - "${DOCKER_PORT_inbox}:2222"
    image: nbisweden/ega-mina-inbox
    volumes:
      - inbox:/ega/inbox
EOF
else
cat >> ${PRIVATE}/lega.yml <<EOF  # SFTP inbox
    environment:
      - CEGA_ENDPOINT=http://cega-users
      - CEGA_ENDPOINT_CREDS=lega:${CEGA_REST_PASSWORD}
      - CEGA_ENDPOINT_JSON_PREFIX=
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    image: nbisweden/ega-inbox:dev
    volumes:
      - ./lega/conf.ini:/etc/ega/conf.ini:ro
      - inbox:/ega/inbox
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
  # Stable ID mapper
  id-mapper:
    depends_on:
      - db
      - mq
    image: nbisweden/ega-base:dev
    container_name: id-mapper
    volumes:
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-id-mapper"]

  # Ingestion Workers
  ingest:
    depends_on:
      - db
      - mq
    image: nbisweden/ega-base:dev
    container_name: ingest
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - inbox:/ega/inbox
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-ingest"]

  # Key server
  keys:
    hostname: keys
    container_name: keys
    image: nbisweden/ega-base:dev
    expose:
      - "8443"
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - KEYS_PASSWORD=${KEYS_PASSWORD}
    volumes:
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
       - ./lega/keys.ini.enc:/etc/ega/keys.ini.enc:ro
       - ./lega/certs/ssl.cert:/etc/ega/ssl.cert:ro
       - ./lega/certs/ssl.key:/etc/ega/ssl.key:ro
       - ./lega/pgp/ega.sec:/etc/ega/pgp/ega.sec:ro
       - ./lega/pgp/ega2.sec:/etc/ega/pgp/ega2.sec:ro
    restart: on-failure:3
    external_links:
      - cega-eureka:cega-eureka
    networks:
      - lega
      - cega
    entrypoint: ["gosu","lega","ega-keyserver","--keys","/etc/ega/keys.ini.enc"]

  # Quality Control
  verify:
    depends_on:
      - db
      - mq
      - keys
    hostname: verify
    container_name: verify
    image: nbisweden/ega-base:dev
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-verify"]

  # S3
  s3:
    hostname: s3
    container_name: s3
    image: minio/minio
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY}
    volumes:
      - s3:/data
    restart: on-failure:3
    networks:
      - lega
    # ports:
    #   - "${DOCKER_PORT_s3}:9000"
    command: server /data

# Use the default driver for volume creation
volumes:
  db:
  inbox:
  s3:
EOF

#########################################################################
# Keeping a trace of if
#########################################################################

cat >> ${PRIVATE}/lega/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/instance.sh for INSTANCE lega
#
#####################################################################
#
PGP_PASSPHRASE            = ${PGP_PASSPHRASE}
PGP_NAME                  = ${PGP_NAME}
PGP_COMMENT               = ${PGP_COMMENT}
PGP_EMAIL                 = ${PGP_EMAIL}
SSL_SUBJ                  = ${SSL_SUBJ}
#
DB_USER                   = ${DB_USER}
DB_PASSWORD               = ${DB_PASSWORD}
#
CEGA_MQ_USER              = lega
CEGA_MQ_PASSWORD          = ${CEGA_MQ_PASSWORD}
CEGA_REST_PASSWORD        = ${CEGA_REST_PASSWORD}
#
S3_ACCESS_KEY             = ${S3_ACCESS_KEY}
S3_SECRET_KEY             = ${S3_SECRET_KEY}
#
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_mq            = ${DOCKER_PORT_mq}
DOCKER_PORT_s3            = ${DOCKER_PORT_s3}
DOCKER_PORT_kibana        = ${DOCKER_PORT_kibana}
#
LEGA_PASSWORD             = ${LEGA_PASSWORD}
KEYS_PASSWORD             = ${KEYS_PASSWORD}
EOF
