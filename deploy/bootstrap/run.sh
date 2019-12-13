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
ARCHIVE_BACKEND=posix
HOSTNAME_DOMAIN='' #".localega"

PYTHONEXEC=python

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value>     \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--archive-backend <value> \tSelect the archive backend: S3 or POSIX [Default: ${ARCHIVE_BACKEND}]"
    echo -e "\t--pythonexec <value>  \tPython execute command [Default: ${PYTHONEXEC}]"
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
        --archive-backend) ARCHIVE_BACKEND=${2,,}; shift;;
        --pythonexec) PYTHONEXEC=$2; shift;;
        --domain) HOSTNAME_DOMAIN=${2,,}; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3
[[ -x $(readlink ${PYTHONEXEC}) ]] && echo "${PYTHONEXEC} is not executable. Adjust the setting with --pythonexec" && exit 3

#########################################################################

source ${HERE}/defs.sh

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}
exec 2>${PRIVATE}/.err

mkdir -p ${PRIVATE}/{keys,logs,confs}
chmod 700 ${PRIVATE}/{keys,logs,confs}

#########################################################################
echo -n "Bootstrapping "
[[ "${VERBOSE}" == 'yes' ]] && echo "" # new line

echomsg "\t* Loading the settings"
source ${HERE}/settings.rc

#########################################################################

echomsg "\t* Fake Central EGA parameters"
# For the fake CEGA
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

#########################################################################

echomsg "\t* Fake Central EGA users"
source ${HERE}/users.sh

#########################################################################

backup ${DOT_ENV}

cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=lega
COMPOSE_FILE=${PRIVATE}/lega.yml:${PRIVATE}/cega.yml
COMPOSE_PATH_SEPARATOR=:
EOF

#########################################################################

echomsg "\t* the C4GH key"

# C4GH_PASSPHRASE is an env var
cat > ${PRIVATE}/keys/c4gh_keygen.sh <<EOF
set timeout -1
spawn crypt4gh-keygen -f --pk ${PRIVATE}/keys/ega.pub --sk ${PRIVATE}/keys/ega.sec
expect "Passphrase for *"
send -- "${C4GH_PASSPHRASE}\r"
expect eof
EOF
expect -f ${PRIVATE}/keys/c4gh_keygen.sh &>/dev/null
rm -f ${PRIVATE}/keys/c4gh_keygen.sh

# Making the key readable, because when it's injected inside the container
# it retains the permissions. Therefore, originally 400, will make it unreadable to the lega user.
chmod 444 ${PRIVATE}/keys/ega.sec

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

# For the fake CentralEGA and the testsuite
yes | make -C ${HERE}/certs cega testsuite OPENSSL=${OPENSSL} DOMAIN="${HOSTNAME_DOMAIN}" &>${PRIVATE}/.err

#########################################################################

echomsg "\t* Configuration files"

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



cat > ${PRIVATE}/confs/ingest.ini <<EOF
[DEFAULT]

[inbox]
location = /ega/inbox/%s/
chroot_sessions = True

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
EOF

if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
    cat >> ${PRIVATE}/confs/ingest.ini <<EOF

[archive]
storage_driver = S3Storage
s3_url = https://archive${HOSTNAME_DOMAIN}:9000
s3_access_key = ${S3_ACCESS_KEY}
s3_secret_key = ${S3_SECRET_KEY}
#region = lega
cacertfile = /etc/ega/CA.cert
certfile = /etc/ega/ssl.cert
keyfile = /etc/ega/ssl.key
EOF
else
    # POSIX file system
    cat >> ${PRIVATE}/confs/ingest.ini <<EOF

[archive]
storage_driver = FileStorage
location = /ega/archive/%s/
EOF
fi

cat > ${PRIVATE}/confs/verify.ini <<EOF
[DEFAULT]

master_key = c4gh_file

[c4gh_file]
loader_class = C4GHFileKey
passphrase = ${C4GH_PASSPHRASE}
filepath = /etc/ega/ega.sec

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
EOF

if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
    cat >> ${PRIVATE}/confs/verify.ini <<EOF

[archive]
storage_driver = S3Storage
s3_url = https://archive${HOSTNAME_DOMAIN}:9000
s3_access_key = ${S3_ACCESS_KEY}
s3_secret_key = ${S3_SECRET_KEY}
#region = lega
cacertfile = /etc/ega/CA.cert
certfile = /etc/ega/ssl.cert
keyfile = /etc/ega/ssl.key

EOF
else
    # POSIX file system
    cat >> ${PRIVATE}/confs/verify.ini <<EOF

[archive]
storage_driver = FileStorage
location = /ega/archive/%s/

EOF
fi


cat > ${PRIVATE}/confs/finalize.ini <<EOF
[DEFAULT]

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
EOF



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
    restart: on-failure:3
    networks:
      - lega
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

  # Ingestion Workers
  ingest:
    environment:
      - LEGA_LOG=debug
    hostname: ingest${HOSTNAME_DOMAIN}
    image: egarchive/lega-base:latest
    container_name: ingest${HOSTNAME_DOMAIN}
    volumes:
      # - ../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - inbox:/ega/inbox
      - ./confs/ingest.ini:/etc/ega/conf.ini:ro
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
    # entrypoint: ["/bin/sleep", "1000000000000"]

  # Consistency Control
  verify:
    environment:
      - LEGA_LOG=debug
    hostname: verify${HOSTNAME_DOMAIN}
    container_name: verify${HOSTNAME_DOMAIN}
    image: egarchive/lega-base:latest
    volumes:
      # - ../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ./confs/verify.ini:/etc/ega/conf.ini:ro
      - ./keys/ega.sec:/etc/ega/ega.sec
      - ./entrypoint.sh:/usr/local/bin/lega-entrypoint.sh
      - ../bootstrap/certs/data/verify.cert.pem:/etc/ega/ssl.cert
      - ../bootstrap/certs/data/verify.sec.pem:/etc/ega/ssl.key
      - ../bootstrap/certs/data/CA.verify.cert.pem:/etc/ega/CA.cert
EOF
if [[ ${ARCHIVE_BACKEND} == 'posix' ]]; then
    cat >> ${PRIVATE}/lega.yml <<EOF
      - archive:/ega/archive
EOF
else
    cat >> ${PRIVATE}/lega.yml <<EOF
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
EOF
fi

cat >> ${PRIVATE}/lega.yml <<EOF
    restart: on-failure:3
    networks:
      - lega
    user: lega
    entrypoint: ["lega-entrypoint.sh"]
    command: ["ega-verify"]
    # entrypoint: ["/bin/sleep", "1000000000000"]

  # Stable ID mapper
  finalize:
    environment:
      - LEGA_LOG=debug
    hostname: finalize${HOSTNAME_DOMAIN}
    image: egarchive/lega-base:latest
    container_name: finalize${HOSTNAME_DOMAIN}
    volumes:
      # - ../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ./confs/finalize.ini:/etc/ega/conf.ini:ro
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
    # entrypoint: ["/bin/sleep", "1000000000000"]

EOF

if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
cat >> ${PRIVATE}/lega.yml <<EOF

  # Storage backend: S3
  archive:
    hostname: archive${HOSTNAME_DOMAIN}
    container_name: archive${HOSTNAME_DOMAIN}
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
    volumes:
      - ../../tests/_common/users.py:/cega/users.py
      - ../../tests/_common/users:/cega/users
      - ../bootstrap/certs/data/cega-users.cert.pem:/cega/ssl.crt
      - ../bootstrap/certs/data/cega-users.sec.pem:/cega/ssl.key
      - ../bootstrap/certs/data/CA.cega-users.cert.pem:/cega/CA.crt
    networks:
      - lega
    user: root
    entrypoint: ["python", "/cega/users.py", "0.0.0.0", "443", "/cega/users"]

  cega-mq:
    hostname: cega-mq${HOSTNAME_DOMAIN}
    ports:
      - "15670:15672"
      - "5670:5671"
    image: rabbitmq:3.7.8-management-alpine
    container_name: cega-mq${HOSTNAME_DOMAIN}
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


#########################################################################
# Keeping a trace of if
#########################################################################

cat > ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/boot.sh
#
#####################################################################
#
C4GH_PASSPHRASE           = ${C4GH_PASSPHRASE}
#
# Database users are 'lega_in' and 'lega_out'
DB_LEGA_IN_PASSWORD       = ${DB_LEGA_IN_PASSWORD}
DB_LEGA_OUT_PASSWORD      = ${DB_LEGA_OUT_PASSWORD}
#
# Central EGA mq and user credentials
CEGA_CONNECTION           = ${CEGA_CONNECTION}
CEGA_ENDPOINT_CREDS       = ${CEGA_USERS_CREDS}
#
# Local Message Broker (used by mq and inbox)
MQ_USER                   = ${MQ_USER}
MQ_PASSWORD               = ${MQ_PASSWORD}
MQ_CONNECTION             = ${MQ_CONNECTION}?${MQ_CONNECTION_PARAMS}
MQ_EXCHANGE               = cega
MQ_ROUTING_KEY            = files.inbox
#
# Port mappings
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_mq            = ${DOCKER_PORT_mq}
EOF

if [[ ${ARCHIVE_BACKEND} == 's3' ]]; then
cat >>  ${PRIVATE}/.trace <<EOF
DOCKER_PORT_s3            = ${DOCKER_PORT_s3}
#
S3_ACCESS_KEY             = ${S3_ACCESS_KEY}
S3_SECRET_KEY             = ${S3_SECRET_KEY}
EOF
fi

task_complete "Bootstrap complete"
