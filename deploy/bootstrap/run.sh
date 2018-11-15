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
# PYTHON=python
source ${HERE}/defs.sh

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}/{secrets,confs}
exec 2>${PRIVATE}/.err
backup ${DOT_ENV}
cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
COMPOSE_FILE=private/lega.yml
#COMPOSE_IGNORE_ORPHANS=1
EOF
# Don't use ${PRIVATE}, since it's running in a container: wrong path then.

#########################################################################
echomsg "Generating private data for a LocalEGA instance"

echo "secrets:" > ${PRIVATE}/secrets.yml
source ${HERE}/settings.rc

# Special case for development only
S3_ACCESS_KEY=$(<${PRIVATE}/secrets/s3_access_key)
S3_SECRET_KEY=$(<${PRIVATE}/secrets/s3_secret_key)
AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}

#########################################################################
echomsg "\t* the keys"

# Generate the LocalEGA main key (Format: PKCS8, SSH2, or None)
crypt4gh generate -o ${PRIVATE}/ega.key -P "${EC_KEY_PASSPHRASE}" -f none
chmod 644 ${PRIVATE}/ega.key.pub
add_secret 'ega.sec' $(<${PRIVATE}/ega.key)

crypt4gh generate -o ${PRIVATE}/ega.signing.key -P "${EC_KEY_PASSPHRASE}" --signing -f none
chmod 644 ${PRIVATE}/ega.signing.key.pub
add_secret 'ega.signing.key' $(<${PRIVATE}/ega.signing.key)

# ssh-keygen -t ed25519 \
# 	   -f ${PRIVATE}/ega.sign.key \
# 	   -m PKCS8 \
# 	   -b 256 \
# 	   -P "${EC_SIGN_KEY_PASSPHRASE}" \
# 	   -C "LocalEGA-signing@CRG"

# echo -n ${EC_KEY_PASSPHRASE} > ${PRIVATE}/secrets/ec_key_passphrase
# openssl genpkey -algorithm X25519 -out ${PRIVATE}/ega.key -pass ${PRIVATE}/secrets/ec_key_passphrase
# rm -f ${PRIVATE}/secrets/ec_key_passphrase

# 224 ec bits == 2048 rsa bits

#########################################################################
echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/outgest.key -nodes \
	   -out ${PRIVATE}/outgest.cert \
	   -sha256 \
	   -days 1000 \
	   -subj ${SSL_SUBJ}

#########################################################################
echomsg "\t* the configuration files"

cat > ${PRIVATE}/confs/ingest.ini <<EOF
[inbox]
location = /ega/inbox/%s

[vault]
##############################
# Backed by POSIX file system
#############################
# driver = FileStorage
# location = /ega/vault
# mode = 2750

###########################
# Backed by S3
###########################
driver = S3Storage
url = http://vault:9000
access_key = /run/secrets/s3_access_key
secret_key = /run/secrets/s3_secret_key
region = lega
bucket = lega

[broker]
host = mq
port = 5672
connection_attempts = 30
retry = 30
retry_delay = 1
username = admin
password = /run/secrets/lega_mq_password
vhost = /
enable_ssl = no
heartbeat = 0

[db]
host = db
port = 5432
user = lega_in
password = /run/secrets/db_lega_in
database = lega
try = 30
try_interval = 1
sslmode = require
EOF

cat > ${PRIVATE}/confs/verify.ini <<EOF
[DEFAULT]
private_key = /etc/ega/ega.sec

[vault]
##############################
# Backed by POSIX file system
#############################
# driver = FileStorage
# location = /ega/vault
# mode = 2750

###########################
# Backed by S3
###########################
driver = S3Storage
url = http://vault:9000
access_key = /run/secrets/s3_access_key
secret_key = /run/secrets/s3_secret_key
region = lega
bucket = lega

[broker]
host = mq
port = 5672
connection_attempts = 30
retry_delay = 10
username = admin
password = /run/secrets/lega_mq_password
vhost = /
enable_ssl = no
heartbeat = 0

[db]
host = db
port = 5432
user = lega_in
password = /run/secrets/db_lega_in
database = lega
try = 30
try_interval = 1
sslmode = require
EOF

cat > ${PRIVATE}/confs/finalize.ini <<EOF
[broker]
host = mq
port = 5672
connection_attempts = 30
retry = 30
retry_delay = 10
username = admin
password = /run/secrets/lega_mq_password
vhost = /
enable_ssl = no
heartbeat = 0

[db]
host = db
port = 5432
user = lega_in
password = /run/secrets/db_lega_in
database = lega
try = 30
try_interval = 1
sslmode = require
EOF

cat > ${PRIVATE}/confs/outgest.ini <<EOF
[DEFAULT]
host = 0.0.0.0
port = 8443
enable_ssl = no
ssl_certfile = /etc/ega/ssl.cert
ssl_keyfile = /etc/ega/ssl.key

permissions_endpoint = https://egatest.crg.eu/permissions/files/%s
streamer_endpoint = http://streamer:8443/

# Operation timeout in seconds. [Default: 5min]
timeout = 300
EOF

cat > ${PRIVATE}/confs/streamer.ini <<EOF
[DEFAULT]
host = 0.0.0.0
port = 8443
private_key = /etc/ega/ega.sec
signing_key = /etc/ega/signing.key

[vault]
##############################
# Backed by POSIX file system
#############################
# driver = FileStorage
# location = /ega/vault
# mode = 2750

###########################
# Backed by S3
###########################
driver = S3Storage
url = http://vault:9000
access_key = /run/secrets/s3_access_key
secret_key = /run/secrets/s3_secret_key
region = lega
bucket = lega

[db]
host = db
port = 5432
user = lega_out
password = /run/secrets/db_lega_out
database = lega
try = 30
try_interval = 1
sslmode = require
EOF

cat > ${PRIVATE}/confs/inbox.ini <<EOF
[DEFAULT]
location = /ega/inbox/%s
chroot_sessions = True

[broker]
host = mq
port = 5672
connection_attempts = 30
retry = 30
retry_delay = 10
username = admin
password = /run/secrets/lega_mq_password
vhost = /
enable_ssl = no
heartbeat = 0
EOF

#########################################################################
echomsg "Configuring the local RabbitMQ"

LEGA_MQ_PASSWORD_HASH=$(get_secret 'lega_mq_password' | python3.6 /tmp/rabbitmq_hash.py)

cat > ${PRIVATE}/defs.json <<EOF
{"rabbit_version":"3.7.8",
 "users":[{"name":"${LEGA_MQ_USER}","password_hash":"${LEGA_MQ_PASSWORD_HASH}","hashing_algorithm":"rabbit_password_hashing_sha256","tags":"administrator"}],
 "vhosts":[{"name":"/"}],
 "permissions":[{"user":"${LEGA_MQ_USER}","vhost":"/","configure":".*","write":".*","read":".*"}],
 "parameters":[],
 "global_parameters":[{"name":"cluster_name","value":"rabbit@localhost"}],
 "policies":[],
 "queues":[{"name":"files","vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	   {"name":"archived","vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	   {"name":"stableIDs","vhost":"/","durable":true,"auto_delete":false,"arguments":{}}],
 "exchanges":[{"name":"lega","vhost":"/","type":"topic","durable":true,"auto_delete":false,"internal":false,"arguments":{}},
              {"name":"cega","vhost":"/","type":"topic","durable":true,"auto_delete":false,"internal":false,"arguments":{}}],
 "bindings":[{"source":"lega", "vhost":"/", "destination":"archived",  "destination_type":"queue", "routing_key":"archived", "arguments":{}}]
}
EOF

#########################################################################
echomsg "Creating the docker-compose file (Version 3.7)"

cat >> ${PRIVATE}/lega.yml <<EOF
version: '3.7'

# Use the default driver for network creation
networks:
  lega-external:
  lega-internal:
  lega-private:

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
    secrets:
      - source: cega_connection
        target: cega_connection
        uid: 'rabbitmq'
        gid: 'rabbitmq'
        mode: 0600
    hostname: mq
    image: rabbitmq:3.7.8-management
    container_name: mq
    ports:
      - "15672:15672"
    networks:
      - lega-internal
    volumes:
      - ../images/mq/entrypoint.sh:/usr/bin/lega-entrypoint.sh
      - ./defs.json:/etc/rabbitmq/defs.json:ro
    entrypoint: ["/bin/bash", "/usr/bin/lega-entrypoint.sh"]
    command: ["rabbitmq-server"]

  # Postgres Database (using default port 5432)
  db:
    secrets:
      - source: db_lega_in
        target: db_lega_in
        uid: 'postgres'
        gid: 'postgres'
        mode: 0600
      - source: db_lega_out
        target: db_lega_out
        uid: 'postgres'
        gid: 'postgres'
        mode: 0600
    environment:
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
      - ../images/db/grants.sql:/docker-entrypoint-initdb.d/grants.sql:ro
      - ../images/db/entrypoint.sh:/usr/bin/lega-entrypoint.sh
    networks:
      - lega-private
    entrypoint: ["/bin/bash", "/usr/bin/lega-entrypoint.sh"]

  # SFTP inbox
  inbox:
    hostname: inbox
    environment:
      - CEGA_USERS_ENDPOINT=https://egatest.crg.eu/lega/v1/legas/users/
      - CEGA_USERS_JSON_PREFIX=response.result
      - LEGA_LOG=debug
    secrets:
      - cega_users.creds
      - lega_mq_password
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    container_name: inbox
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}inbox
    volumes:
      - ./confs/inbox.ini:/etc/ega/conf.ini:ro
      - inbox:/ega/inbox
      - ../images/inbox/entrypoint.sh:/usr/bin/lega-entrypoint.sh
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_auth:/root/_auth
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-external
      - lega-internal
    entrypoint: ["/bin/bash", "/usr/bin/lega-entrypoint.sh"]

  # Ingestion Workers
  ingest:
    environment:
      - LEGA_LOG=debug
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    container_name: ingest
    secrets:
      - source: db_lega_in
        target: db_lega_in
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_access_key
        target: s3_access_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_secret_key
        target: s3_secret_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: lega_mq_password
        target: lega_mq_password
        uid: 'lega'
        gid: 'lega'
        mode: 0600
    volumes:
       - inbox:/ega/inbox
       - ./confs/ingest.ini:/etc/ega/conf.ini:ro
       - ./defs.json:/etc/rabbitmq/defs.json:ro
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
       - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
       - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-internal
      - lega-private
    entrypoint: ["gosu", "lega", "lega-ingest"]

  # Checksum validation
  verify:
    environment:
      - LEGA_LOG=debug
    hostname: verify
    container_name: verify
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    secrets:
      - source: db_lega_in
        target: db_lega_in
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_access_key
        target: s3_access_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_secret_key
        target: s3_secret_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: lega_mq_password
        target: lega_mq_password
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: ega.sec
        target: /etc/ega/ega.sec
        uid: 'lega'
        gid: 'lega'
        mode: 0400
    volumes:
      - ./confs/verify.ini:/etc/ega/conf.ini:ro
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-internal
      - lega-private
    entrypoint: ["gosu", "lega", "lega-verify"]

  # Stable ID mapper, and inbox clean up
  finalize:
    environment:
      - LEGA_LOG=debug
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    container_name: finalize
    secrets:
      - source: db_lega_in
        target: db_lega_in
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: lega_mq_password
        target: lega_mq_password
        uid: 'lega'
        gid: 'lega'
        mode: 0600
    volumes:
      - ./confs/finalize.ini:/etc/ega/conf.ini:ro
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-internal
      - lega-private
    entrypoint: ["gosu", "lega", "lega-finalize"]

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
      - lega-private
    command: server /data

  # HTTP Data-Edge (using OpenID Connect + Permissions Server)
  outgest:
    environment:
      - LEGA_LOG=debug
    hostname: outgest
    container_name: outgest
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    ports:
      - "${DOCKER_PORT_outgest}:8443"
    volumes:
      - ./confs/outgest.ini:/etc/ega/conf.ini:ro
      - ./outgest.cert:/etc/ega/ssl.cert
      - ./outgest.key:/etc/ega/ssl.key
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-external
      - lega-internal
    entrypoint: ["gosu", "lega", "lega-outgest"]

  # Re-Encryption
  streamer:
    environment:
      - LEGA_LOG=debug
    hostname: streamer
    container_name: streamer
    image: ${DOCKER_IMAGE_PREFIX:-egarchive/}lega
    secrets:
      - source: db_lega_out
        target: db_lega_out
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_access_key
        target: s3_access_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: s3_secret_key
        target: s3_secret_key
        uid: 'lega'
        gid: 'lega'
        mode: 0600
      - source: ega.sec
        target: /etc/ega/ega.sec
        uid: 'lega'
        gid: 'lega'
        mode: 0400
      - source: ega.signing.key
        target: /etc/ega/signing.key
        uid: 'lega'
        gid: 'lega'
        mode: 0400
    volumes:
      - ./confs/streamer.ini:/etc/ega/conf.ini:ro
EOF
if [[ "${DEPLOY_DEV}" = "yes" ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - ~/_ega/lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ~/_cryptor/crypt4gh:/home/lega/.local/lib/python3.6/site-packages/crypt4gh
EOF
fi
cat >> ${PRIVATE}/lega.yml <<EOF
    networks:
      - lega-internal
      - lega-private
    entrypoint: ["gosu", "lega", "lega-streamer"]

EOF

# Adding the secrets
cat ${PRIVATE}/secrets.yml >> ${PRIVATE}/lega.yml

#########################################################################
echomsg "Keeping a trace"

cat >> ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/instance.sh for INSTANCE lega
#
#####################################################################
#
EC_KEY_PASSPHRASE         = $(<${PRIVATE}/secrets/ec_key_passphrase)
EC_KEY_PATH               = ${PRIVATE}/secrets/ega.key{,.pub}
EC_SIGN_KEY_PASSPHRASE    = $(<${PRIVATE}/secrets/ec_sign_key_passphrase)
EC_SIGN_KEY_PATH          = ${PRIVATE}/secrets/ega.signing.key{,.pub}
#
SSL_SUBJ                  = ${SSL_SUBJ}
#
# Database users are 'lega_in' and 'lega_out'
DB_LEGA_IN_PASSWORD       = $(<${PRIVATE}/secrets/db_lega_in)
DB_LEGA_OUT_PASSWORD      = $(<${PRIVATE}/secrets/db_lega_out)
#
CEGA_CONNECTION           = $(<${PRIVATE}/secrets/cega_connection)
CEGA_USERS_CREDS          = $(<${PRIVATE}/secrets/cega_users.creds)
LEGA_MQ_PASSWORD          = $(<${PRIVATE}/secrets/lega_mq_password)
#
S3_ACCESS_KEY             = ${S3_ACCESS_KEY}
S3_SECRET_KEY             = ${S3_SECRET_KEY}
#
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_outgest       = ${DOCKER_PORT_outgest}
EOF

#########################################################################
task_complete "Bootstrap complete"
