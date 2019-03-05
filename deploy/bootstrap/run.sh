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
KEYSERVER=lega
REAL_CEGA=no

GEN_KEY=${EXTRAS}/generate_pgp_key.py
PYTHONEXEC=python

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value>     \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--inbox <value>       \tSelect inbox \"openssh\" or \"mina\" [Default: ${INBOX}]"
    echo -e "\t--keyserver <value>   \tSelect keyserver \"lega\" or \"ega\" [Default: ${KEYSERVER}]"
    echo -e "\t--inbox-backend <value>   \tSelect the inbox backend: S3 or POSIX [Default: ${INBOX_BACKEND}]"
    echo -e "\t--genkey <value>      \tPath to PGP key generator [Default: ${GEN_KEY}]"
    echo -e "\t--pythonexec <value>  \tPython execute command [Default: ${PYTHONEXEC}]"
    echo -e "\t--with-real-cega      \tUse the real Central EGA Message broker and Authentication Service"
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
        --keyserver) KEYSERVER=${2,,}; shift;;
        --genkey) GEN_KEY=$2; shift;;
        --pythonexec) PYTHONEXEC=$2; shift;;
        --with-real-cega) REAL_CEGA=yes;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
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
    CEGA_CONNECTION=$'amqp://legatest:legatest@cega-mq:5672/lega'
    CEGA_USERS_ENDPOINT=$'http://cega-users/lega/v1/legas/users'
    CEGA_USERS_CREDS=$'legatest:legatest'
fi

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

source ${HERE}/settings.rc

#########################################################################

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

[archive]
storage_driver = S3Storage
s3_url = http://archive:9000
s3_access_key = ${S3_ACCESS_KEY}
s3_secret_key = ${S3_SECRET_KEY}
#region = lega

EOF

if [[ ${INBOX_BACKEND} == 's3' ]]; then
    cat >> ${PRIVATE}/conf.ini <<EOF
[inbox]
storage_driver = S3Storage
url = http://inbox-s3-backend:9000
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
      - CEGA_MQ_CONNECTION=${CEGA_CONNECTION}
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    image: egarchive/lega-inbox:latest
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
      - inbox:/ega/inbox
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
  # Stable ID mapper
  finalize:
    depends_on:
      - db
      - mq
    image: egarchive/lega-base:latest
    container_name: finalize
    labels:
        lega_label: "finalize"
    volumes:
      - ./conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega
    user: lega
    entrypoint: ["ega-finalize"]

  # Ingestion Workers
  ingest:
    depends_on:
      - db
      - mq
    image: egarchive/lega-base:latest
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
    user: lega
    entrypoint: ["ega-ingest"]

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
    image: egarchive/lega-base:latest
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
    networks:
      - lega
    user: lega
    entrypoint: ["ega-keyserver","--keys","/etc/ega/keys.ini.enc"]

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
    image: egarchive/lega-base:latest
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
    user: lega
    entrypoint: ["ega-verify"]

  # Data Out re-encryption service
  res:
    depends_on:
      - archive
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
      - EGA_EBI_AWS_ENDPOINT_URL=http://archive:${DOCKER_PORT_s3}
      - EGA_EBI_AWS_ENDPOINT_REGION=
    volumes:
      - ./pgp/ega.shared.pass:/etc/ega/pgp/ega.shared.pass:ro
    restart: on-failure:3
    networks:
      - lega

  # Storage backend: S3
  archive:
    hostname: archive
    container_name: archive
    labels:
        lega_label: "archive"
    image: minio/minio:RELEASE.2018-12-19T23-46-24Z
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY}
    volumes:
      - archive:/data
    restart: on-failure:3
    networks:
      - lega
    # ports:
    #   - "${DOCKER_PORT_s3}:9000"
    command: server /data

EOF

if [[ ${INBOX_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF
  # Inbox S3 Backend Storage
  inbox-s3-backend:
    hostname: inbox-s3-backend
    container_name: inbox-s3-backend
    labels:
        lega_label: "inbox-s3-backend"
    image: minio/minio:RELEASE.2018-12-19T23-46-24Z
    environment:
      - MINIO_ACCESS_KEY=${S3_ACCESS_KEY_INBOX}
      - MINIO_SECRET_KEY=${S3_SECRET_KEY_INBOX}
    volumes:
      - inbox-s3:/data
    restart: on-failure:3
    networks:
      - lega
    ports:
      - "${DOCKER_PORT_s3_inbox}:9000"
    command: server /data
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
  cega-mq:
    hostname: cega-mq
    ports:
      - "15670:15672"
      - "5670:5672"
    image: rabbitmq:3.6.14-management
    container_name: cega-mq
    labels:
        lega_label: "cega-mq"
    volumes:
       - ./cega-mq-defs.json:/etc/rabbitmq/defs.json:ro
       - ./cega-mq-rabbitmq.config:/etc/rabbitmq/rabbitmq.config:ro
    restart: on-failure:3
    networks:
      - lega

  cega-users:
    hostname: cega-users
    ports:
      - "15671:80"
    image: egarchive/lega-base:latest
    container_name: cega-users
    labels:
        lega_label: "cega-users"
    volumes:
       - ../../tests/_common/users.py:/cega/users.py
       - ../../tests/_common/users.json:/cega/users.json
    networks:
      - lega
    entrypoint: ["python", "/cega/users.py", "0.0.0.0", "80", "/cega/users.json"]
EOF

    # The user/password is legatest:legatest
    cat > ${PRIVATE}/cega-mq-defs.json <<EOF
{"rabbit_version":"3.6.14",
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
	  {disk_free_limit, "1GB"}]},
 {rabbitmq_management, [ {load_definitions, "/etc/rabbitmq/defs.json"} ]}
].
EOF
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
