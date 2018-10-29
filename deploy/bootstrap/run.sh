#!/usr/bin/env bash
set -e

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../private
DOT_ENV=${HERE}/../.env

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl
COMPOSE_PROJECT_NAME=crg

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value> \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--prefix <value>  \tPrefix used for the project name [Default: ${COMPOSE_PROJECT_NAME}]"
    echo ""
    echo -e "\t--verbose, -v     \tShow verbose output"
    echo -e "\t--polite, -p      \tDo not force the re-creation of the subfolders. Ask instead"
    echo -e "\t--help, -h        \tOutputs this message and exits"
    echo -e "\t-- ...            \tAny other options appearing after the -- will be ignored"
    echo ""
}


# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage; exit 0;;
        --verbose|-v) VERBOSE=yes;;
        --polite|-p) FORCE=no;;
        --openssl) OPENSSL=$2; shift;;
        --prefix) COMPOSE_PROJECT_NAME=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

#########################################################################
source ${HERE}/defs.sh

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}
exec 2>${PRIVATE}/.err
backup ${DOT_ENV}
cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
COMPOSE_FILE=private/lega.yml
#COMPOSE_IGNORE_ORPHANS=1
EOF
# Don't use ${PRIVATE}, since it's running in a container: wrong path then.

#########################################################################
source ${HERE}/settings.rc

#########################################################################
# Generate the configuration for each instance
echomsg "Generating private data for a LocalEGA instance"
#########################################################################

echomsg "\t* the keys"

# Generate the LocalEGA main key
crypt4gh generate -f ${PRIVATE}/ega.key -P "${EC_KEY_PASSPHRASE}"
chmod 644 ${PRIVATE}/ega.key.pub

crypt4gh generate -f ${PRIVATE}/ega.signing.key -P "${EC_KEY_PASSPHRASE}" --signing
chmod 644 ${PRIVATE}/ega.signing.key.pub

# ssh-keygen -t ed25519 \
# 	   -f ${PRIVATE}/ega.key \
# 	   -b 256 \
# 	   -P "${EC_KEY_PASSPHRASE}" \
# 	   -C "${EC_KEY_COMMENT}"

# ssh-keygen -t ed25519 \
# 	   -f ${PRIVATE}/ega.sign.key \
# 	   -b 256 \
# 	   -P "${EC_SIGN_KEY_PASSPHRASE}" \
# 	   -C "${EC_SIGN_KEY_COMMENT}"

# 224 ec bits == 2048 rsa bits


#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/outgest.key -nodes \
	   -out ${PRIVATE}/outgest.cert \
	   -sha256 \
	   -days 1000 \
	   -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* conf.ini"
cat > ${PRIVATE}/conf.ini <<EOF
[DEFAULT]
log = debug
#log = silent

[inbox]
location = /ega/inbox/%s
chroot_sessions = True

[vault]
driver = S3Storage
url = http://vault:9000
access_key = ${S3_ACCESS_KEY}
secret_key = ${S3_SECRET_KEY}
#region = lega

[broker]
host = mq
connection_attempts = 30
retry_delay = 10
username = admin
password = ${LEGA_MQ_PASSWORD}
vhost = /


[db]
host = db
port = 5432
user = lega_in
password = ${DB_LEGA_IN_PASSWORD}
database = lega
try = 30
sslmode = require

[verify]
private_key = /etc/ega/ega.sec

[outgestion]
port = 8443
enable_ssl = no
ssl_certfile = /etc/ega/ssl.cert
ssl_keyfile = /etc/ega/ssl.key

permissions_endpoint = https://egatest.crg.eu/permissions/files/%s
streamer_endpoint = http://streamer:8443/

[streamer]
host = 0.0.0.0
port = 8443
private_key = /etc/ega/ega.sec
signing_key = /etc/ega/signing.key

[db_out]
host = db
port = 5432
user = lega_out
password = ${DB_LEGA_OUT_PASSWORD}
database = lega
try = 30
sslmode = require
EOF

#########################################################################
# Creating the docker-compose file (Version 3.2)
#########################################################################
cat >> ${PRIVATE}/lega.yml <<EOF
version: '3'

# Use the default driver for network creation
networks:
  lega:
  lega-internal:

# Use the default driver for volume creation
volumes:
  db:
  inbox:
  vault:

services:

  ############################################
  # Local EGA instance
  ############################################

  # Local Message broker
  mq:
    environment:
      - CEGA_CONNECTION=${CEGA_CONNECTION}
      - LEGA_MQ_PASSWORD=${LEGA_MQ_PASSWORD}
    hostname: mq
    image: rabbitmq:3.7.8-management
    container_name: mq
    ports:
      - "15672:15672"
    networks:
      - lega-internal
    volumes:
      - ../images/mq/entrypoint.sh:/usr/bin/ega-entrypoint.sh
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]
    command: ["rabbitmq-server"]

  # Postgres Database (using default port 5432)
  db:
    environment:
      - DB_LEGA_IN_PASSWORD=${DB_LEGA_IN_PASSWORD}
      - DB_LEGA_OUT_PASSWORD=${DB_LEGA_OUT_PASSWORD}
      - PGDATA=/ega/data
      - SSL_SUBJ=${SSL_SUBJ}
    hostname: db
    container_name: db
    image: postgres:11
    volumes:
      - db:/ega/data
      - ../images/db/postgresql.conf:/etc/ega/pg.conf:ro
      - ../images/db/main.sql:/docker-entrypoint-initdb.d/main.sql:ro
      - ../images/db/download.sql:/docker-entrypoint-initdb.d/download.sql:ro
      - ../images/db/qc.sql:/docker-entrypoint-initdb.d/qc.sql:ro
      - ../images/db/data-out-extensions.sql:/docker-entrypoint-initdb.d/data-out-extensions.sql:ro
      - ../images/db/grants.sql:/docker-entrypoint-initdb.d/grants.sql:ro
      - ../images/db/entrypoint.sh:/usr/bin/ega-entrypoint.sh
    networks:
      - lega-internal
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]

  # SFTP inbox
  inbox:
    hostname: ega-inbox
    environment:
      - CEGA_ENDPOINT=https://egatest.crg.eu/lega/v1/legas/users/
      - CEGA_ENDPOINT_CREDS=lega1:${CEGA_REST_PASSWORD}
      - CEGA_ENDPOINT_JSON_PREFIX=response.result
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    container_name: inbox
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}inbox
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - inbox:/ega/inbox
      - ../images/inbox/entrypoint.sh:/usr/bin/ega-entrypoint.sh
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_auth:/root/_auth
    networks:
      - lega
#    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]

  # Ingestion Workers
  ingest:
    # depends_on:
    #   - mq
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    container_name: ingest
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - inbox:/ega/inbox
       - ./conf.ini:/etc/ega/conf.ini:ro
       - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
       - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
    networks:
      - lega-internal
    entrypoint: ["gosu", "lega", "ega-ingest"]

  # Checksum validation
  verify:
    hostname: verify
    container_name: verify
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ./ega.key.pub:/etc/ega/ega.pub:ro
      - ./ega.key:/etc/ega/ega.sec:ro
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
    networks:
      - lega-internal
    entrypoint: ["gosu", "lega", "ega-verify"]

  # Stable ID mapper, and inbox clean up
  finalize:
    # depends_on:
    #   - mq
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    container_name: finalize
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
    networks:
      - lega-internal
    entrypoint: ["gosu", "lega", "ega-finalize"]

  # Here we use S3
  vault:
    hostname: vault
    container_name: vault
    image: minio/minio
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY}
    volumes:
      - vault:/data
    networks:
      - lega-internal
    command: server /data

  # HTTP Data-Edge (using OpenID Connect + Permissions Server)
  outgest:
    hostname: outgest
    container_name: outgest
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    ports:
      - "${DOCKER_PORT_outgest}:8443"
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ./outgest.cert:/etc/ega/ssl.cert
      - ./outgest.key:/etc/ega/ssl.key
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
    networks:
      - lega
      - lega-internal
    entrypoint: ["gosu", "lega", "ega-outgest"]

  # Re-Encryption
  streamer:
    hostname: streamer
    container_name: streamer
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ./ega.key.pub:/etc/ega/ega.pub:ro
      - ./ega.key:/etc/ega/ega.sec:ro
      - ./ega.signing.key:/etc/ega/signing.key:ro
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
    networks:
      - lega-internal
    entrypoint: ["gosu", "lega", "ega-streamer"]
EOF

#########################################################################
# Keeping a trace
#########################################################################

cat >> ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/instance.sh for INSTANCE lega
#
#####################################################################
#
EC_KEY_COMMENT            = ${EC_KEY_COMMENT}
EC_KEY_PASSPHRASE         = ${EC_KEY_PASSPHRASE}
EC_SIGN_KEY_COMMENT       = ${EC_SIGN_KEY_COMMENT}
EC_SIGN_KEY_PASSPHRASE    = ${EC_SIGN_KEY_PASSPHRASE}
#
SSL_SUBJ                  = ${SSL_SUBJ}
#
# Database users are 'lega_in' and 'lega_out'
DB_LEGA_IN_PASSWORD       = ${DB_LEGA_IN_PASSWORD}
DB_LEGA_OUT_PASSWORD      = ${DB_LEGA_OUT_PASSWORD}
#
CEGA_CONNECTION           = amqps://lega1:A6P32r2KUSY7BPvL@hellgate.crg.eu:5271/lega1
CEGA_REST_PASSWORD        = ${CEGA_REST_PASSWORD}
LEGA_MQ_PASSWORD          = ${LEGA_MQ_PASSWORD}
#
S3_ACCESS_KEY             = ${S3_ACCESS_KEY}
S3_SECRET_KEY             = ${S3_SECRET_KEY}
#
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_outgest       = ${DOCKER_PORT_outgest}
EOF

task_complete "Bootstrap complete"
