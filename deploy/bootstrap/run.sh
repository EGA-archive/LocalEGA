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
INBOX_BACKEND=posix
ARCHIVE_BACKEND=s3
REAL_CEGA=no
HOSTNAME_DOMAIN='' #".localega"

GEN_KEY=${EXTRAS}/generate_pgp_key.py
PYTHONEXEC=python

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value>     \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--inbox <value>       \tSelect inbox \"openssh\" or \"mina\" [Default: ${INBOX}]"
    echo -e "\t--inbox-backend <value>   \tSelect the inbox backend: S3 or POSIX [Default: ${INBOX_BACKEND}]"
    echo -e "\t--archive-backend <value> \tSelect the archive backend: S3 or POSIX [Default: ${ARCHIVE_BACKEND}]"
    echo -e "\t--genkey <value>      \tPath to PGP key generator [Default: ${GEN_KEY}]"
    echo -e "\t--pythonexec <value>  \tPython execute command [Default: ${PYTHONEXEC}]"
    echo -e "\t--with-real-cega      \tUse the real Central EGA Message broker and Authentication Service"
    echo -e "\t--domain <value>      \tDomain for the hostnames [Default: '${HOSTNAME_DOMAIN}']"
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
        --inbox) INBOX=${2,,}; shift;;
        --inbox-backend) INBOX_BACKEND=${2,,}; shift;;
        --archive-backend) ARCHIVE_BACKEND=${2,,}; shift;;
        --genkey) GEN_KEY=$2; shift;;
        --pythonexec) PYTHONEXEC=$2; shift;;
        --with-real-cega) REAL_CEGA=yes;;
        --domain) HOSTNAME_DOMAIN=${2,,}; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

#########################################################################

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${HERE}/defs.sh

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}
exec 2>${PRIVATE}/.err

#########################################################################

if [[ ${REAL_CEGA} != 'yes' ]]; then
    # Reset the variables here
    CEGA_CONNECTION_PARAMS=$(${PYTHONEXEC} -c "from urllib.parse import urlencode;                               \
	  			        print(urlencode({ 'heartbeat': 0,                                 \
				                          'connection_attempts': 30,                      \
				                          'retry_delay': 10,                              \
							  'server_name_indication': 'cega-mq${HOSTNAME_DOMAIN}',   \
							  'verify': 'verify_peer',                        \
							  'fail_if_no_peer_cert': 'true',                 \
							  'cacertfile': '/etc/rabbitmq/CA.cert',          \
							  'certfile': '/etc/rabbitmq/ssl.cert',           \
							  'keyfile': '/etc/rabbitmq/ssl.key',             \
				                  }, safe='/-_.'))")

    CEGA_CONNECTION="amqps://legatest:legatest@cega-mq${HOSTNAME_DOMAIN}:5671/lega?${CEGA_CONNECTION_PARAMS}"
    CEGA_USERS_ENDPOINT="https://cega-users${HOSTNAME_DOMAIN}/lega/v1/legas/users"
    CEGA_USERS_CREDS=$'legatest:legatest'
fi

source ${HERE}/settings.rc

# Make sure the variables are set
[[ -z "${CEGA_USERS_ENDPOINT}" ]] && echo 'Environment CEGA_USERS_ENDPOINT is empty' 1>&2 && exit 1
[[ -z "${CEGA_USERS_CREDS}" ]] && echo 'Environment CEGA_USERS_CREDS is empty' 1>&2 && exit 1
[[ -z "${CEGA_CONNECTION}" ]] && echo 'Environment CEGA_CONNECTION is empty' 1>&2 && exit 1

#########################################################################

backup ${DOT_ENV}

if [[ {REAL_CEGA} == 'yes' ]]; then
    cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=lega
COMPOSE_FILE=${PRIVATE}/lega.yml
EOF
else
    cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=lega
COMPOSE_FILE=${PRIVATE}/lega.yml:${PRIVATE}/cega.yml
COMPOSE_PATH_SEPARATOR=:
EOF
fi

#########################################################################

mkdir -p $PRIVATE/{pgp,logs}
chmod 700 $PRIVATE/{pgp,logs}

echomsg "\t* the PGP key"

${PYTHONEXEC} ${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/pgp/ega.pub --priv ${PRIVATE}/pgp/ega.sec --armor
chmod 644 ${PRIVATE}/pgp/ega.pub

${PYTHONEXEC} ${GEN_KEY} "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/pgp/ega2.pub --priv ${PRIVATE}/pgp/ega2.sec --armor
chmod 644 ${PRIVATE}/pgp/ega2.pub

echo -n ${PGP_PASSPHRASE} > ${PRIVATE}/pgp/ega.sec.pass
echo -n ${PGP_PASSPHRASE} > ${PRIVATE}/pgp/ega2.sec.pass
echo -n ${LEGA_PASSWORD} > ${PRIVATE}/pgp/ega.shared.pass

#########################################################################

echomsg "\t* Entrypoint"

# This script is used to go around a feature (bug?) of docker.
# When the /etc/ega/ssl.key is injected,
# it is owned by the host user that injected it.
# On Travis, it's the travis (2000) user.
# It needs to be 600 or less, meaning no group nor world access.
#
# In other words, the lega user cannot read that file.
#
# So we use the following trick.
# We make:
#     * /etc/ega/ssl.key world-readable.
#     * /etc/ega owned by the lega group (so we can write a file in it)
# and then, we copy /etc/ega/ssl.key to /etc/ega/ssl.key.lega
# But this time, owned by lega, and with 400 permissions
#
# This should not be necessary for the deployment
# as they are capable of injecting a file with given owner and permissions.
#

cat > ${PRIVATE}/entrypoint.sh <<'EOF'
#!/bin/sh
set -e
cp /etc/ega/ssl.key /etc/ega/ssl.key.lega
chmod 400 /etc/ega/ssl.key.lega
exec $@
EOF
chmod +x ${PRIVATE}/entrypoint.sh

#########################################################################
echomsg "\t* the SSL certificates"

make -C ${HERE}/certs clean prepare OPENSSL=${OPENSSL} &>${PRIVATE}/.err
yes | make -C ${HERE}/certs OPENSSL=${OPENSSL} DOMAIN="${HOSTNAME_DOMAIN}" &>${PRIVATE}/.err

if [[ ${REAL_CEGA} != 'yes' ]]; then
    yes | make -C ${HERE}/certs cega testsuite OPENSSL=${OPENSSL} DOMAIN="${HOSTNAME_DOMAIN}" &>${PRIVATE}/.err
fi

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

[keyserver]
port = 8080

[quality_control]
keyserver_endpoint = http://keys${HOSTNAME_DOMAIN}:8080/keys/retrieve/%s/private/bin?idFormat=hex

[outgestion]
# Just for test
keyserver_endpoint = http://keys${HOSTNAME_DOMAIN}:8080/keys/retrieve/%s/private/bin?idFormat=hex
EOF

# Local broker connection
MQ_CONNECTION_PARAMS=$(${PYTHONEXEC} -c "from urllib.parse import urlencode;                   \
			          print(urlencode({ 'heartbeat': 0,                     \
				                    'connection_attempts': 30,          \
				                    'retry_delay': 10,                  \
				                  }))")

# Pika is not parsing the URL the way RabbitMQ likes.
# So we add the parameters on the configuration file and
# create the SSL socket ourselves
# Some parameters can be passed in the URL, though.
MQ_CONNECTION="amqps://${MQ_USER}:${MQ_PASSWORD}@mq${HOSTNAME_DOMAIN}:5671/%2F"

# Database connection
DB_CONNECTION_PARAMS=$(${PYTHONEXEC} -c "from urllib.parse import urlencode;                   \
			          print(urlencode({ 'application_name': 'LocalEGA',     \
				                    'sslmode': 'verify-full',           \
				                    'sslcert': '/etc/ega/ssl.cert',     \
				                    'sslkey': '/etc/ega/ssl.key.lega',  \
				                    'sslrootcert': '/etc/ega/CA.cert',  \
				                  }, safe='/-_.'))")

DB_CONNECTION="postgres://lega_in:${DB_LEGA_IN_PASSWORD}@db${HOSTNAME_DOMAIN}:5432/lega"

#
# Configuration file
#

cat >> ${PRIVATE}/conf.ini <<EOF

## Connecting to Local EGA
[broker]
connection = ${MQ_CONNECTION}?${MQ_CONNECTION_PARAMS}

enable_ssl = yes
verify_peer = yes
verify_hostname = no

cacertfile = /etc/ega/CA.cert
certfile = /etc/ega/ssl.cert
keyfile = /etc/ega/ssl.key

[db]
connection = ${DB_CONNECTION}?${DB_CONNECTION_PARAMS}
try = 30
try_interval = 1

[archive]
EOF
if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
    cat >> ${PRIVATE}/conf.ini <<EOF
storage_driver = S3Storage
s3_url = https://archive${HOSTNAME_DOMAIN}:9000
s3_access_key = ${S3_ACCESS_KEY}
s3_secret_key = ${S3_SECRET_KEY}
#region = lega
EOF
else
    # POSIX file system
    cat >> ${PRIVATE}/conf.ini <<EOF
storage_driver = FileStorage
location = /ega/archive/%s/
EOF
fi

if [[ ${INBOX_BACKEND} == 's3' ]]; then
    cat >> ${PRIVATE}/conf.ini <<EOF

[inbox]
storage_driver = S3Storage
url = https://inbox-s3-backend${HOSTNAME_DOMAIN}:9000
access_key = ${S3_ACCESS_KEY_INBOX}
secret_key = ${S3_SECRET_KEY_INBOX}
#region = lega
EOF
else
    # Default: POSIX file system
    cat >> ${PRIVATE}/conf.ini <<EOF

[inbox]
location = /ega/inbox/%s/
chroot_sessions = True
EOF
fi

#########################################################################
# Specifying the LocalEGA components in the docke-compose file
#########################################################################
cat > ${PRIVATE}/lega.yml <<EOF
version: '3.2'

networks:
  lega:
    # user overlay in swarm mode
    # default is bridge
    driver: bridge

# Use the default driver for volume creation
volumes:
  mq:
  db:
  inbox:
  archive:
EOF

if [[ ${INBOX_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
  inbox-s3:
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF

services:

  ############################################
  # Local EGA instance
  ############################################

  # Local Message broker
  mq:
    environment:
      - CEGA_CONNECTION=${CEGA_CONNECTION}
      - MQ_USER=${MQ_USER}
      - MQ_PASSWORD_HASH=${MQ_PASSWORD_HASH}
      - MQ_CA=/etc/rabbitmq/CA.cert
      - MQ_SERVER_CERT=/etc/rabbitmq/ssl.cert
      - MQ_SERVER_KEY=/etc/rabbitmq/ssl.key
    hostname: mq${HOSTNAME_DOMAIN}
    ports:
      - "${DOCKER_PORT_mq}:15672"
    image: egarchive/lega-mq:latest
    container_name: mq${HOSTNAME_DOMAIN}
    labels:
        lega_label: "mq"
    restart: on-failure:3
    networks:
      - lega
    volumes:
      - mq:/var/lib/rabbitmq
      - ../bootstrap/certs/data/mq.cert.pem:/etc/rabbitmq/ssl.cert
      - ../bootstrap/certs/data/mq.sec.pem:/etc/rabbitmq/ssl.key
      - ../bootstrap/certs/data/CA.mq.cert.pem:/etc/rabbitmq/CA.cert

  # Local Database
  db:
    environment:
      - DB_LEGA_IN_PASSWORD=${DB_LEGA_IN_PASSWORD}
      - DB_LEGA_OUT_PASSWORD=${DB_LEGA_OUT_PASSWORD}
      - PGDATA=/ega/data
      - PG_SERVER_CERT=/etc/ega/pg.cert
      - PG_SERVER_KEY=/etc/ega/pg.key
      - PG_CA=/etc/ega/CA.cert
      - PG_VERIFY_PEER=1
    hostname: db${HOSTNAME_DOMAIN}
    container_name: db${HOSTNAME_DOMAIN}
    labels:
        lega_label: "db"
    image: egarchive/lega-db:latest
    volumes:
      - db:/ega/data
      - ../bootstrap/certs/data/db.cert.pem:/etc/ega/pg.cert
      - ../bootstrap/certs/data/db.sec.pem:/etc/ega/pg.key
      - ../bootstrap/certs/data/CA.db.cert.pem:/etc/ega/CA.cert
    restart: on-failure:3
    networks:
      - lega

  # SFTP inbox
  inbox:
    hostname: inbox${HOSTNAME_DOMAIN}
    depends_on:
      - mq
    # Required external link
    container_name: inbox${HOSTNAME_DOMAIN}
    labels:
        lega_label: "inbox"
    restart: on-failure:3
    networks:
      - lega
EOF
if [[ $INBOX == 'mina' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
    environment:
      - CEGA_ENDPOINT=${CEGA_USERS_ENDPOINT%/}/%s?idType=username
      - CEGA_ENDPOINT_CREDS=${CEGA_USERS_CREDS}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY_INBOX}
      - S3_SECRET_KEY=${S3_SECRET_KEY_INBOX}
      - S3_ENDPOINT=inbox-s3-backend:9000
      - USE_SSL=false
    ports:
      - "${DOCKER_PORT_inbox}:2222"
    image: nbisweden/ega-mina-inbox
    volumes:
      - inbox:/ega/inbox
EOF
else
cat >> ${PRIVATE}/lega.yml <<EOF  # SFTP inbox
    environment:
      - CEGA_ENDPOINT=${CEGA_USERS_ENDPOINT}
      - CEGA_ENDPOINT_CREDS=${CEGA_USERS_CREDS}
      - CEGA_ENDPOINT_JSON_PREFIX=response.result
      - MQ_CONNECTION=${MQ_CONNECTION}
      - MQ_EXCHANGE=cega
      - MQ_ROUTING_KEY=files.inbox
      - MQ_VERIFY_PEER=yes
      - MQ_VERIFY_HOSTNAME=no
      - MQ_CA=/etc/ega/CA.cert
      - MQ_CLIENT_CERT=/etc/ega/ssl.cert
      - MQ_CLIENT_KEY=/etc/ega/ssl.key
      - AUTH_VERIFY_PEER=yes
      - AUTH_VERIFY_HOSTNAME=yes
      - AUTH_CA=/etc/ega/CA.cert
      - AUTH_CLIENT_CERT=/etc/ega/ssl.cert
      - AUTH_CLIENT_KEY=/etc/ega/ssl.key
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    image: egarchive/lega-inbox:latest
    volumes:
      - inbox:/ega/inbox
      - ../bootstrap/certs/data/inbox.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/inbox.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.inbox.cert.pem:/etc/ega/CA.cert
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF

  # Ingestion Workers
  ingest:
    hostname: ingest${HOSTNAME_DOMAIN}
    depends_on:
      - db
      - mq
    image: egarchive/lega-base:latest
    container_name: ingest${HOSTNAME_DOMAIN}
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
      - ./entrypoint.sh:/usr/local/bin/lega-entrypoint.sh
      - ../bootstrap/certs/data/ingest.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/ingest.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.ingest.cert.pem:/etc/ega/CA.cert
EOF
if [[ ${ARCHIVE_BACKEND} == 'posix' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - archive:/ega/archive
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
    restart: on-failure:3
    networks:
      - lega
    user: lega
    entrypoint: ["lega-entrypoint.sh"]
    command: ["ega-ingest"]

  # Consistency Control
  verify:
    depends_on:
      - db
      - mq
      - keys
    hostname: verify${HOSTNAME_DOMAIN}
    container_name: verify${HOSTNAME_DOMAIN}
    labels:
        lega_label: "verify"
    image: egarchive/lega-base:latest
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ./entrypoint.sh:/usr/local/bin/lega-entrypoint.sh
      - ../bootstrap/certs/data/verify.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/verify.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.verify.cert.pem:/etc/ega/CA.cert
EOF
if [[ ${ARCHIVE_BACKEND} == 'posix' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
      - archive:/ega/archive
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
    restart: on-failure:3
    networks:
      - lega
    user: lega
    entrypoint: ["lega-entrypoint.sh"]
    command: ["ega-verify"]

  # Stable ID mapper
  finalize:
    hostname: finalize${HOSTNAME_DOMAIN}
    depends_on:
      - db
      - mq
    image: egarchive/lega-base:latest
    container_name: finalize${HOSTNAME_DOMAIN}
    labels:
        lega_label: "finalize"
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - ./entrypoint.sh:/usr/local/bin/lega-entrypoint.sh
      - ../bootstrap/certs/data/finalize.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/finalize.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.finalize.cert.pem:/etc/ega/CA.cert
    restart: on-failure:3
    networks:
      - lega
    user: lega
    entrypoint: ["lega-entrypoint.sh"]
    command: ["ega-finalize"]

  # Key server
  keys:
    hostname: keys${HOSTNAME_DOMAIN}
    container_name: keys${HOSTNAME_DOMAIN}
    labels:
        lega_label: "keys"
    restart: on-failure:3
    networks:
      - lega
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
      - ../bootstrap/certs/data/keys.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/keys.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.keys.cert.pem:/etc/ega/CA.cert
EOF

if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF

  # Storage backend: S3
  archive:
    hostname: archive${HOSTNAME_DOMAIN}
    container_name: archive${HOSTNAME_DOMAIN}
    labels:
        lega_label: "archive"
    image: minio/minio:RELEASE.2018-12-19T23-46-24Z
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY}
    volumes:
      - archive:/data
      - ../bootstrap/certs/data/archive.cert.pem:/root/.minio/certs/public.crt
      - ../bootstrap/certs/data/archive.sec.pem:/root/.minio/certs/private.key
      - ../bootstrap/certs/data/CA.archive.cert.pem:/root/.minio/CAs/LocalEGA.crt
    restart: on-failure:3
    networks:
      - lega
    # ports:
    #   - "${DOCKER_PORT_s3}:9000"
    command: ["server", "/data"]
EOF
fi

if [[ ${INBOX_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF

  # Inbox S3 Backend Storage
  inbox-s3-backend:
    hostname: inbox-s3-backend${HOSTNAME_DOMAIN}
    container_name: inbox-s3-backend${HOSTNAME_DOMAIN}
    labels:
        lega_label: "inbox-s3-backend"
    image: minio/minio:RELEASE.2018-12-19T23-46-24Z
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY_INBOX}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY_INBOX}
      - ../bootstrap/certs/data/inbox-s3-backend.cert.pem:/root/.minio/certs/public.crt
      - ../bootstrap/certs/data/inbox-s3-backend.sec.pem:/root/.minio/certs/private.key
      - ../bootstrap/certs/data/CA.inbox-s3-backend.cert.pem:/home/.minio/CAs/LocalEGA.crt
    volumes:
      - inbox-s3:/data
    restart: on-failure:3
    networks:
      - lega
    ports:
      - "${DOCKER_PORT_s3_inbox}:9000"
    command: ["server", "/data"]
EOF
fi

if [[ ${REAL_CEGA} != 'yes' ]]; then

    #########################################################################
    # Specifying a fake Central EGA broker if requested
    #########################################################################
    cat > ${PRIVATE}/cega.yml <<EOF
############################################
# Faking Central EGA MQ and Users 
# on the lega network, for simplicity
############################################

version: '3.2'

services:

  cega-users:
    hostname: cega-users${HOSTNAME_DOMAIN}
    ports:
      - "15671:443"
    image: egarchive/lega-base:latest
    container_name: cega-users${HOSTNAME_DOMAIN}
    labels:
        lega_label: "cega-users"
    volumes:
      - ../../tests/_common/users.py:/cega/users.py
      - ../../tests/_common/users.json:/cega/users.json
      - ../bootstrap/certs/data/cega-users.cert.pem:/cega/ssl.crt
      - ../bootstrap/certs/data/cega-users.sec.pem:/cega/ssl.key
      - ../bootstrap/certs/data/CA.cega-users.cert.pem:/cega/CA.crt
    networks:
      - lega
    user: root
    entrypoint: ["python", "/cega/users.py", "0.0.0.0", "443", "/cega/users.json"]

  cega-mq:
    hostname: cega-mq${HOSTNAME_DOMAIN}
    ports:
      - "15670:15672"
      - "5670:5671"
    image: rabbitmq:3.7.8-management-alpine
    container_name: cega-mq${HOSTNAME_DOMAIN}
    labels:
        lega_label: "cega-mq"
    volumes:
      - ./cega-mq-defs.json:/etc/rabbitmq/defs.json
      - ./cega-mq-rabbitmq.config:/etc/rabbitmq/rabbitmq.config
      - ./cega-entrypoint.sh:/usr/local/bin/cega-entrypoint.sh
      - ../bootstrap/certs/data/cega-mq.cert.pem:/etc/rabbitmq/ssl.cert
      - ../bootstrap/certs/data/cega-mq.sec.pem:/etc/rabbitmq/ssl.key
      - ../bootstrap/certs/data/CA.cega-mq.cert.pem:/etc/rabbitmq/CA.cert
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["/usr/local/bin/cega-entrypoint.sh"]
EOF

    # The user/password is legatest:legatest
    cat > ${PRIVATE}/cega-mq-defs.json <<EOF
{"rabbit_version":"3.7.8",
 "users":[{"name":"legatest","password_hash":"P9snZluoiHj2JeGqrDYmUHGLu637Qo7Fjgn5wakpk4jCyvcO","hashing_algorithm":"rabbit_password_hashing_sha256","tags":"administrator"}],
 "vhosts":[{"name":"lega"}],
 "permissions":[{"user":"legatest", "vhost":"lega", "configure":".*", "write":".*", "read":".*"}],
 "parameters":[],
 "global_parameters":[{"name":"cluster_name", "value":"rabbit@localhost"}],
 "policies":[],
 "queues":[{"name":"v1.files",            "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}},
	   {"name":"v1.files.inbox",      "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}},
           {"name":"v1.stableIDs",        "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}},
	   {"name":"v1.files.completed",  "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}},
	   {"name":"v1.files.processing", "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}},
	   {"name":"v1.files.error",      "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{}}],
 "exchanges":[{"name":"localega.v1", "vhost":"lega", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}],
 "bindings":[{"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.stableIDs"       ,"routing_key":"stableIDs"},
	     {"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.files"           ,"routing_key":"files"},
	     {"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.files.inbox"     ,"routing_key":"files.inbox"},
	     {"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.files.error"     ,"routing_key":"files.error"},
	     {"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.files.processing","routing_key":"files.processing"},
	     {"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{},"destination":"v1.files.completed" ,"routing_key":"files.completed"}]
}
EOF

    cat > ${PRIVATE}/cega-mq-rabbitmq.config <<EOF
%% -*- mode: erlang -*-
%%
[{rabbit,[{loopback_users, [ ] },
	  {tcp_listeners, [ ]},
	  {ssl_listeners, [5671]},
	  {ssl_options, [{cacertfile, "/etc/rabbitmq/CA.cert"},
                         {certfile,   "/etc/rabbitmq/ssl.cert"},
          		 {keyfile,    "/etc/rabbitmq/ssl.key"},
			 {verify,     verify_peer},
			 {fail_if_no_peer_cert, true}]}
 	  ]},
 {rabbitmq_management, [ {load_definitions, "/etc/rabbitmq/defs.json"} ]}
].
EOF

    cat > ${PRIVATE}/cega-entrypoint.sh <<EOF
#!/bin/bash
chown rabbitmq:rabbitmq /etc/rabbitmq/*
find /var/lib/rabbitmq \! -user rabbitmq -exec chown rabbitmq '{}' +
exec docker-entrypoint.sh rabbitmq-server
EOF
    chmod +x ${PRIVATE}/cega-entrypoint.sh
fi


#########################################################################
# Keeping a trace of if
#########################################################################

cat >> ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/boot.sh
#
#####################################################################
#
PGP_PASSPHRASE            = ${PGP_PASSPHRASE}
PGP_NAME                  = ${PGP_NAME}
PGP_COMMENT               = ${PGP_COMMENT}
PGP_EMAIL                 = ${PGP_EMAIL}
#
# Database users are 'lega_in' and 'lega_out'
DB_LEGA_IN_PASSWORD       = ${DB_LEGA_IN_PASSWORD}
DB_LEGA_OUT_PASSWORD      = ${DB_LEGA_OUT_PASSWORD}
#
# Central EGA mq and user credentials
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
#
# Local Message Broker (used by mq and inbox)
MQ_USER                   = ${MQ_USER}
MQ_PASSWORD               = ${MQ_PASSWORD}
MQ_CONNECTION             = ${MQ_CONNECTION}?${MQ_CONNECTION_PARAMS}
MQ_EXCHANGE               = cega
MQ_ROUTING_KEY            = files.inbox
EOF

if [[ ${INBOX_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/.trace <<EOF
#
# Inbox S3 backend
DOCKER_PORT_s3_inbox      = ${DOCKER_PORT_s3_inbox}
S3_ACCESS_KEY_INBOX       = ${S3_ACCESS_KEY_INBOX}
S3_SECRET_KEY_INBOX       = ${S3_SECRET_KEY_INBOX}
EOF
fi

task_complete "Bootstrap complete"
