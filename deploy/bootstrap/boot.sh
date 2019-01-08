#!/usr/bin/env bash
set -e

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../private
DOT_ENV=${HERE}/../.env
EXTRAS=${HERE}/../../extras

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl
INBOX=openssh
KEYSERVER=lega

GEN_KEY=${EXTRAS}/generate_pgp_key.py
PYTHONEXEC=python

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value> \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--inbox <value>   \tSelect inbox \"openssh\" or \"mina\" [Default: ${INBOX}]"
    echo -e "\t--keyserver <value>   \tSelect keyserver \"lega\" or \"ega\" [Default: ${KEYSERVER}]"
    echo -e "\t--genkey <value>   \tPath to PGP key generator [Default: ${GEN_KEY}]"
    echo -e "\t--pythonexec <value>   \tPython execute command [Default: ${PYTHONEXEC}]"
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
        --inbox) INBOX=$2; shift;;
        --keyserver) KEYSERVER=$2; shift;;
        --genkey) GEN_KEY=$2; shift;;
        --pythonexec) PYTHONEXEC=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${HERE}/defs.sh

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}
exec 2>${PRIVATE}/.err
backup ${DOT_ENV}

cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=lega
COMPOSE_FILE=${PRIVATE}/lega.yml
#COMPOSE_PATH_SEPARATOR=:
EOF

source ${HERE}/settings.rc

mkdir -p $PRIVATE/{pgp,certs,logs}
chmod 700 $PRIVATE/{pgp,certs,logs}

echomsg "\t* the PGP key"

${PYTHONEXEC} ${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/pgp/ega.pub --priv ${PRIVATE}/pgp/ega.sec --armor
chmod 644 ${PRIVATE}/pgp/ega.pub

${PYTHONEXEC} ${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/pgp/ega2.pub --priv ${PRIVATE}/pgp/ega2.sec --armor
chmod 644 ${PRIVATE}/pgp/ega2.pub

echo -n ${PGP_PASSPHRASE} > ${PRIVATE}/pgp/ega.sec.pass
echo -n ${PGP_PASSPHRASE} > ${PRIVATE}/pgp/ega2.sec.pass
echo -n ${LEGA_PASSWORD} > ${PRIVATE}/pgp/ega.shared.pass

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/certs/ssl.key -nodes -out ${PRIVATE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.ini"
${OPENSSL} enc -aes-256-cbc -salt -out ${PRIVATE}/keys.ini.enc -md md5 -k ${KEYS_PASSWORD} <<EOF
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
cat > ${PRIVATE}/conf.ini <<EOF
[DEFAULT]
log = debug
#log = silent

EOF
if [[ $KEYSERVER == 'ega' ]]; then
cat >> ${PRIVATE}/conf.ini <<EOF

[keyserver]
port = 8080

[quality_control]
keyserver_endpoint = http://keys:8080/keys/retrieve/%s/private/bin?idFormat=hex

[outgestion]
# Just for test
keyserver_endpoint = http://keys:8080/keys/retrieve/%s/private/bin?idFormat=hex
EOF
else
cat >> ${PRIVATE}/conf.ini <<EOF
[keyserver]
port = 8443

[quality_control]
keyserver_endpoint = https://keys:8443/retrieve/%s/private

[outgestion]
# Just for test
keyserver_endpoint = https://keys:8443/retrieve/%s/private
EOF
fi
cat >> ${PRIVATE}/conf.ini <<EOF

[inbox]
location = /ega/inbox/%s
chroot_sessions = True

[vault]
driver = S3Storage
url = http://vault:9000
access_key = ${S3_ACCESS_KEY}
secret_key = ${S3_SECRET_KEY}
#region = lega

## Connecting to Local EGA
[broker]
host = mq
connection_attempts = 30
# delay in seconds
retry_delay = 10

[postgres]
host = db
port = 5432
user = lega_in
password = ${DB_LEGA_IN_PASSWORD}
database = lega
try = 30
sslmode = require

[eureka]
endpoint = http://cega-eureka:8761
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

services:

  ############################################
  # Local EGA instance
  ############################################

  # Local Message broker
  mq:
    environment:
      - CEGA_CONNECTION=${CEGA_CONNECTION}
    hostname: mq
    ports:
      - "${DOCKER_PORT_mq}:15672"
    image: rabbitmq:3.6.14-management
    container_name: mq
    labels:
        lega_label: "mq"
    restart: on-failure:3
    networks:
      - lega
    volumes:
      - ../images/mq/defs.json:/etc/rabbitmq/defs.json
      - ../images/mq/rabbitmq.config:/etc/rabbitmq/rabbitmq.config
      - ../images/mq/entrypoint.sh:/usr/bin/ega-entrypoint.sh
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]
    command: ["rabbitmq-server"]

  # Postgres Database
  db:
    environment:
      - DB_LEGA_IN_PASSWORD=${DB_LEGA_IN_PASSWORD}
      - DB_LEGA_OUT_PASSWORD=${DB_LEGA_OUT_PASSWORD}
      - PGDATA=/ega/data
      - SSL_SUBJ=${SSL_SUBJ}
    hostname: db
    container_name: db
    labels:
        lega_label: "db"
    image: postgres:10
    volumes:
      - db:/ega/data
      - ../images/db/postgresql.conf:/etc/ega/pg.conf:ro
      - ../images/db/main.sql:/docker-entrypoint-initdb.d/main.sql:ro
      - ../images/db/grants.sql:/docker-entrypoint-initdb.d/grants.sql:ro
      - ../images/db/audit.sql:/docker-entrypoint-initdb.d/audit.sql:ro
      - ../images/db/download.sql:/docker-entrypoint-initdb.d/download.sql:ro
      - ../images/db/ebi.sql:/docker-entrypoint-initdb.d/ebi.sql:ro
      - ../images/db/qc.sql:/docker-entrypoint-initdb.d/qc.sql:ro
      - ../images/db/entrypoint.sh:/usr/bin/ega-entrypoint.sh
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]


  # SFTP inbox
  inbox:
    hostname: ega-inbox
    depends_on:
      - mq
    # Required external link
    container_name: inbox
    labels:
        lega_label: "inbox"
    restart: on-failure:3
    networks:
      - lega
EOF
if [[ $INBOX == 'mina' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
    environment:
      - CEGA_ENDPOINT=https://egatest.crg.eu/lega/v1/legas/users/%s?idType=username
      - CEGA_ENDPOINT_CREDS=${CEGA_USERS_CREDS}
    ports:
      - "${DOCKER_PORT_inbox}:2222"
    image: nbisweden/ega-mina-inbox
    volumes:
      - inbox:/ega/inbox
EOF
else
cat >> ${PRIVATE}/lega.yml <<EOF  # SFTP inbox
    environment:
      - CEGA_ENDPOINT=https://egatest.crg.eu/lega/v1/legas/users
      - CEGA_ENDPOINT_CREDS=${CEGA_USERS_CREDS}
      - CEGA_ENDPOINT_JSON_PREFIX=response.result
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    image: nbisweden/ega-inbox:latest
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ../images/inbox/entrypoint.sh:/usr/local/bin/entrypoint.sh
      - inbox:/ega/inbox
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
  # Stable ID mapper
  finalize:
    depends_on:
      - db
      - mq
    image: nbisweden/ega-base:latest
    container_name: finalize
    labels:
        lega_label: "finalize"
    volumes:
       - ./conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-id-mapper"]

  # Ingestion Workers
  ingest:
    depends_on:
      - db
      - mq
    image: nbisweden/ega-base:latest
    container_name: ingest
    labels:
        lega_label: "ingest"
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - inbox:/ega/inbox
       - ./conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-ingest"]

  # Key server
EOF
if [[ $KEYSERVER == 'ega' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
  keys:
    hostname: keys
    container_name: keys
    labels:
        lega_label: "keys"
    image: cscfi/ega-keyserver
    environment:
      - SPRING_PROFILES_ACTIVE=no-oss
      - EGA_KEY_PATH=/etc/ega/pgp/ega.sec,/etc/ega/pgp/ega2.sec
      - EGA_KEYPASS_PATH=/etc/ega/pgp/ega.sec.pass,/etc/ega/pgp/ega2.sec.pass
      - EGA_SHAREDPASS_PATH=/etc/ega/pgp/ega.shared.pass
      - EGA_PUBLICKEY_URL=
      - EGA_LEGACY_PATH=
    volumes:
       - ./pgp/ega.sec:/etc/ega/pgp/ega.sec:ro
       - ./pgp/ega.sec.pass:/etc/ega/pgp/ega.sec.pass:ro
       - ./pgp/ega2.sec:/etc/ega/pgp/ega2.sec:ro
       - ./pgp/ega2.sec.pass:/etc/ega/pgp/ega2.sec.pass:ro
       - ./pgp/ega.shared.pass:/etc/ega/pgp/ega.shared.pass:ro
    restart: on-failure:3
    networks:
      - lega

EOF
else
cat >> ${PRIVATE}/lega.yml <<EOF
  keys:
    hostname: keys
    container_name: keys
    labels:
        lega_label: "keys"
    image: nbisweden/ega-base:latest
    expose:
      - "8443"
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - KEYS_PASSWORD=${KEYS_PASSWORD}
    volumes:
       - ./conf.ini:/etc/ega/conf.ini:ro
       - ./keys.ini.enc:/etc/ega/keys.ini.enc:ro
       - ./certs/ssl.cert:/etc/ega/ssl.cert:ro
       - ./certs/ssl.key:/etc/ega/ssl.key:ro
       - ./pgp/ega.sec:/etc/ega/pgp/ega.sec:ro
       - ./pgp/ega2.sec:/etc/ega/pgp/ega2.sec:ro
    restart: on-failure:3
    external_links:
      - cega-eureka:cega-eureka
    networks:
      - lega
    entrypoint: ["gosu","lega","ega-keyserver","--keys","/etc/ega/keys.ini.enc"]

EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
  # Quality Control
  verify:
    depends_on:
      - db
      - mq
      - keys
    hostname: verify
    container_name: verify
    labels:
        lega_label: "verify"
    image: nbisweden/ega-base:latest
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - ./conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-verify"]

  # Data Out re-encryption service
  res:
    depends_on:
      - vault
      - keys
    hostname: res
    container_name: res
    labels:
        lega_label: "res"
    image: cscfi/ega-res
    ports:
      - "${DOCKER_PORT_res}:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=no-oss,LocalEGA
      - EGA_EGA_EXTERNAL_URL=
      - EGA_EGA_CRAM_FASTA_A=
      - EGA_EGA_CRAM_FASTA_B=
      - EGA_EBI_FIRE_URL=
      - EGA_EBI_FIRE_ARCHIVE=
      - EGA_EBI_FIRE_KEY=
      - SERVICE_ARCHIVE_CLASS=
      - EGA_SHAREDPASS_PATH=/etc/ega/pgp/ega.shared.pass
      - EGA_EBI_AWS_ACCESS_KEY=${S3_ACCESS_KEY}
      - EGA_EBI_AWS_ACCESS_SECRET=${S3_SECRET_KEY}
      - EGA_EBI_AWS_ENDPOINT_URL=http://vault:${DOCKER_PORT_s3}
      - EGA_EBI_AWS_ENDPOINT_REGION=
    volumes:
      - ./pgp/ega.shared.pass:/etc/ega/pgp/ega.shared.pass:ro
    restart: on-failure:3
    networks:
      - lega

  # Storage backend: S3
  vault:
    hostname: vault
    container_name: vault
    labels:
        lega_label: "vault"
    image: minio/minio
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY}
    volumes:
      - vault:/data
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
  vault:
EOF

#########################################################################
# Keeping a trace of if
#########################################################################

cat >> ${PRIVATE}/.trace <<EOF
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
# Database users are 'lega_in' and 'lega_out'
DB_LEGA_IN_PASSWORD       = ${DB_LEGA_IN_PASSWORD}
DB_LEGA_OUT_PASSWORD      = ${DB_LEGA_OUT_PASSWORD}
DB_LEGA_IN_USER           = lega_in
DB_LEGA_OUT_USER          = lega_out
#
CEGA_CONNECTION           = ${CEGA_CONNECTION}
CEGA_ENDPOINT_CREDS       = ${CEGA_USERS_CREDS}
#
S3_ACCESS_KEY             = ${S3_ACCESS_KEY}
S3_SECRET_KEY             = ${S3_SECRET_KEY}
#
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_mq            = ${DOCKER_PORT_mq}
DOCKER_PORT_s3            = ${DOCKER_PORT_s3}
DOCKER_PORT_res           = ${DOCKER_PORT_res}
#
LEGA_PASSWORD             = ${LEGA_PASSWORD}
KEYS_PASSWORD             = ${KEYS_PASSWORD}
EOF

task_complete "Bootstrap complete"
