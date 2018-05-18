#!/usr/bin/env bash

[[ -z "${INSTANCE}" ]] && echo 'The variable INSTANCE must be defined' 1>&2 && exit 1

########################################################
# Loading the instance's settings

if [[ -f ${SETTINGS} ]]; then
    source ${SETTINGS}
else
    echo "No settings found for ${INSTANCE}"
    exit 1
fi

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

if [ -z "${DB_USER}" -o "${DB_USER}" == "postgres" ]; then
    echo "Choose a database user (but not 'postgres')"
    exit 4
fi

#########################################################################
# And....cue music
#########################################################################

mkdir -p $PRIVATE/${INSTANCE}/{pgp,rsa,certs,logs}
chmod 700 $PRIVATE/${INSTANCE}/{pgp,rsa,certs,logs}

echomsg "\t* the PGP key"

if [[ -f /tmp/generate_pgp_key.py ]]; then
    # Running in a container
    GEN_KEY="python3.6 /tmp/generate_pgp_key.py"
else
    # Running on host, outside a container
    GEN_KEY="python ${EXTRAS}/generate_pgp_key.py"
fi

# Python 3.6
${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/${INSTANCE}/pgp/ega.pub --priv ${PRIVATE}/${INSTANCE}/pgp/ega.sec --armor
chmod 644 ${PRIVATE}/${INSTANCE}/pgp/ega.pub

${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/${INSTANCE}/pgp/ega2.pub --priv ${PRIVATE}/${INSTANCE}/pgp/ega2.sec --armor
chmod 644 ${PRIVATE}/${INSTANCE}/pgp/ega2.pub

#########################################################################

echomsg "\t* the RSA private key"
${OPENSSL} genpkey -algorithm RSA -pass pass:"${RSA_PASSPHRASE}" -out ${PRIVATE}/${INSTANCE}/rsa/ega.sec -pkeyopt rsa_keygen_bits:2048 -aes-256-cbc
${OPENSSL} genpkey -algorithm RSA -pass pass:"${RSA_PASSPHRASE}" -out ${PRIVATE}/${INSTANCE}/rsa/ega2.sec -pkeyopt rsa_keygen_bits:2048 -aes-256-cbc

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/${INSTANCE}/certs/ssl.key -nodes -out ${PRIVATE}/${INSTANCE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.conf"
cat > ${PRIVATE}/${INSTANCE}/keys.conf <<EOF
[DEFAULT]
rsa : rsa.key.1
pgp : pgp.key.1

[rsa.key.1]
path : /etc/ega/rsa/ega.sec
passphrase : ${RSA_PASSPHRASE}
expire: 30/MAR/19 08:00:00

[rsa.key.2]
path : /etc/ega/rsa/ega2.sec
passphrase : ${RSA_PASSPHRASE}
expire: 30/MAR/19 08:00:00

[pgp.key.1]
path : /etc/ega/pgp/ega.sec
passphrase : ${PGP_PASSPHRASE}
expire: 30/MAR/19 08:00:00

[pgp.key.2]
path : /etc/ega/pgp/ega2.sec
passphrase : ${PGP_PASSPHRASE}
expire: 30/MAR/18 08:00:00
EOF

echomsg "\t* ega.conf"
cat > ${PRIVATE}/${INSTANCE}/ega.conf <<EOF
[DEFAULT]
log = /etc/ega/logger.yml

[ingestion]
# Keyserver communication
keyserver_endpoint_pgp = http://ega-keys-${INSTANCE}:443/retrieve/pgp/%s
keyserver_endpoint_rsa = http://ega-keys-${INSTANCE}:443/active/rsa

decrypt_cmd = python3.6 -u -m lega.openpgp %(file)s

[outgestion]
# Just for test
keyserver_endpoint = https://ega-keys-${INSTANCE}:443/temp/file/%s

## Connecting to Local EGA
[broker]
host = ega-mq-${INSTANCE}

[db]
host = ega-db-${INSTANCE}
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}

[eureka]
endpoint = http://cega-eureka:8761
EOF

# echomsg "\t* SFTP Inbox port"
# cat >> ${DOT_ENV} <<EOF
# DOCKER_PORT_inbox_${INSTANCE}=${DOCKER_PORT_inbox}
# EOF

echomsg "\t* db.sql"
# cat > ${PRIVATE}/${INSTANCE}/db.sql <<EOF
# -- DROP USER IF EXISTS lega;
# -- CREATE USER ${DB_USER} WITH password '${DB_PASSWORD}';
# DROP DATABASE IF EXISTS lega;
# CREATE DATABASE lega WITH OWNER ${DB_USER};

# EOF
if [[ -f /tmp/db.sql ]]; then
    # Running in a container
    cat /tmp/db.sql >> ${PRIVATE}/${INSTANCE}/db.sql
else
    # Running on host, outside a container
    cat ${EXTRAS}/db.sql >> ${PRIVATE}/${INSTANCE}/db.sql
fi
# cat >> ${PRIVATE}/${INSTANCE}/db.sql <<EOF

# -- Changing the owner there too
# ALTER TABLE files OWNER TO ${DB_USER};
# ALTER TABLE users OWNER TO ${DB_USER};
# ALTER TABLE errors OWNER TO ${DB_USER};
# EOF

echomsg "\t* logger.yml"
_LOG_LEVEL=${LOG_LEVEL:-DEBUG}

cat > ${PRIVATE}/${INSTANCE}/logger.yml <<EOF
version: 1
root:
  level: NOTSET
  handlers: [noHandler]

loggers:
  connect:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  ingestion:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  keyserver:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  vault:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  verify:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  socket-utils:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  inbox:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  utils:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  amqp:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  db:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  crypto:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  asyncio:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiopg:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.access:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.client:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.internal:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.server:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.web:
    level: ${_LOG_LEVEL}
    handlers: [logstash]
  aiohttp.websocket:
    level: ${_LOG_LEVEL}
    handlers: [logstash]


handlers:
  noHandler:
    class: logging.NullHandler
    level: NOTSET
  console:
    class: logging.StreamHandler
    formatter: simple
    stream: ext://sys.stdout
  logstash:
    class: lega.utils.logging.LEGAHandler
    formatter: json
    host: ega-logstash-${INSTANCE}
    port: 5600

formatters:
  json:
    (): lega.utils.logging.JSONFormatter
    format: '(asctime) (name) (process) (processName) (levelname) (lineno) (funcName) (message)'
  lega:
    format: '[{asctime:<20}][{name}][{process:d} {processName:>15}][{levelname}] (L:{lineno}) {funcName}: {message}'
    style: '{'
    datefmt: '%Y-%m-%d %H:%M:%S'
  simple:
    format: '[{name:^10}][{levelname:^6}] (L{lineno}) {message}'
    style: '{'
EOF


#########################################################################
# Populate env-settings for docker compose
#########################################################################

echomsg "\t* the docker-compose configuration files"

cat > ${PRIVATE}/${INSTANCE}/db.env <<EOF
DB_INSTANCE=ega-db-${INSTANCE}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=lega
EOF

cat > ${PRIVATE}/${INSTANCE}/pgp.env <<EOF
PGP_EMAIL=${PGP_EMAIL}
PGP_PASSPHRASE=${PGP_PASSPHRASE}
EOF

cat > ${PRIVATE}/${INSTANCE}/cega.env <<EOF
#
LEGA_GREETINGS=${LEGA_GREETINGS}
#
CEGA_ENDPOINT=http://cega-users/user/
CEGA_ENDPOINT_CREDS=${INSTANCE}:${CEGA_REST_PASSWORD}
CEGA_ENDPOINT_JSON_PASSWD=.password_hash
CEGA_ENDPOINT_JSON_PUBKEY=.pubkey
EOF


# For the moment, still using guest:guest
echomsg "\t* Local broker to Central EGA broker credentials"
cat > ${PRIVATE}/${INSTANCE}/mq.env <<EOF
CEGA_CONNECTION=amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega-mq:5672/${INSTANCE}
CEGA_MQ_PASSWORD=${CEGA_MQ_PASSWORD}
EOF


#########################################################################
# Keeping a trace of if
#########################################################################

cat >> ${PRIVATE}/${INSTANCE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/instance.sh for INSTANCE ${INSTANCE}
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
DB_TRY                    = ${DB_TRY}
#
LEGA_GREETINGS            = ${LEGA_GREETINGS}
#
CEGA_MQ_USER              = cega_${INSTANCE}
CEGA_MQ_PASSWORD          = ${CEGA_MQ_PASSWORD}
CEGA_REST_PASSWORD        = ${CEGA_REST_PASSWORD}
#
MINIO_ACCESS_KEY          = ${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY          = ${MINIO_SECRET_KEY}
#
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_mq            = ${DOCKER_PORT_mq}
DOCKER_PORT_minio         = ${DOCKER_PORT_minio}
DOCKER_PORT_kibana        = ${DOCKER_PORT_kibana}
EOF
