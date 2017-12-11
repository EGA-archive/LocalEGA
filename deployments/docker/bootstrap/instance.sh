#!/usr/bin/env bash

[[ -z ${INSTANCE} ]] && echo '${INSTANCE} must be defined' 1>&2 && exit 1

########################################################
# Loading the instance's settings

if [[ -f ${SETTINGS}/${INSTANCE} ]]; then
    source ${SETTINGS}/${INSTANCE}
else
    echo "No settings found for ${INSTANCE}"
    exit 1
fi

[[ -x $(readlink ${GPG}) ]] && echo "${GPG} is not executable. Adjust the setting with --gpg" && exit 2
[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

if [ -z "${DB_USER}" -o "${DB_USER}" == "postgres" ]; then
    echo "Choose a database user (but not 'postgres')"
    exit 4
fi

#########################################################################
# And....cue music
#########################################################################

mkdir -p $PRIVATE/${INSTANCE}/{gpg,rsa,certs,logs}
chmod 700 $PRIVATE/${INSTANCE}/{gpg,rsa,certs,logs}

echomsg "\t* the GnuPG key"

cat > ${PRIVATE}/${INSTANCE}/gen_key <<EOF
%echo Generating a basic OpenPGP key
Key-Type: RSA
Key-Length: 4096
Name-Real: ${GPG_NAME}
Name-Comment: ${GPG_COMMENT}
Name-Email: ${GPG_EMAIL}
Expire-Date: 0
Passphrase: ${GPG_PASSPHRASE}
# Do a commit here, so that we can later print "done" :-)
%commit
%echo done
EOF

${GPG} --homedir ${PRIVATE}/${INSTANCE}/gpg --batch --generate-key ${PRIVATE}/${INSTANCE}/gen_key
chmod 700 ${PRIVATE}/${INSTANCE}/gpg
rm -f ${PRIVATE}/${INSTANCE}/gen_key
${GPG_CONF} --kill gpg-agent

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genrsa -out ${PRIVATE}/${INSTANCE}/rsa/ega.sec -passout pass:${RSA_PASSPHRASE} 2048
${OPENSSL} rsa -in ${PRIVATE}/${INSTANCE}/rsa/ega.sec -passin pass:${RSA_PASSPHRASE} -pubout -out ${PRIVATE}/${INSTANCE}/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/${INSTANCE}/certs/ssl.key -nodes -out ${PRIVATE}/${INSTANCE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.conf"
cat > ${PRIVATE}/${INSTANCE}/keys.conf <<EOF
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = ${RSA_PASSPHRASE}
EOF

echomsg "\t* ega.conf"
cat > ${PRIVATE}/${INSTANCE}/ega.conf <<EOF
[DEFAULT]
#log = debug
log = /etc/ega/logger.yml

[ingestion]
gpg_cmd = gpg2 --decrypt %(file)s

# Keyserver communication
keyserver_host = ega_keys_${INSTANCE}

## Connecting to Local EGA
[local.broker]
host = ega_mq_${INSTANCE}

## Connecting to Central EGA
[cega.broker]
host = cega_mq
username = cega_${INSTANCE}
password = ${CEGA_MQ_PASSWORD}
vhost = ${INSTANCE}
heartbeat = 0

file_queue = ${INSTANCE}.v1.commands.file
file_routing = ${INSTANCE}.completed

[db]
host = ega_db_${INSTANCE}
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}

[frontend]
host = ega_frontend_${INSTANCE}
cega_password = ${CEGA_PASSWORD}

[outgestion]
# Keyserver communication
keyserver_host = ega_keys_${INSTANCE}
EOF

echomsg "\t* SFTP Inbox port"
cat >> ${DOT_ENV} <<EOF
DOCKER_INBOX_${INSTANCE}_PORT=${DOCKER_INBOX_PORT}
EOF

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
    cat ${HERE}/../../../extras/db.sql >> ${PRIVATE}/${INSTANCE}/db.sql
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
  frontend:
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
  sys-monitor:
    level: ${_LOG_LEVEL}
    handlers: [logstash,console]
  user-monitor:
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
    class: lega.utils.logging.LogstashHandler
    formatter: json
    host: ega-logstash-${INSTANCE}
    port: 5000

formatters:
  json:
    format: '{"timeLogged": "%(asctime)s", "name": "%(name)s", "process": "%(process)s", "processName": "%(processName)s", "levelName": "%(levelname)s", "lineNumber": "%(lineno)s", "functionName": "%(funcName)s", "message": "%(message)s"}'
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
DB_INSTANCE=ega_db_${INSTANCE}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=lega
EOF

cat > ${PRIVATE}/${INSTANCE}/gpg.env <<EOF
GPG_EMAIL=${GPG_EMAIL}
GPG_PASSPHRASE=${GPG_PASSPHRASE}
EOF

cat >> ${PRIVATE}/cega/env <<EOF
CEGA_REST_${INSTANCE}_PASSWORD=${CEGA_REST_PASSWORD}
EOF

cat > ${PRIVATE}/${INSTANCE}/cega.env <<EOF
#
LEGA_GREETINGS=${LEGA_GREETINGS}
#
CEGA_ENDPOINT=http://cega_users/user/%s
CEGA_ENDPOINT_USER=${INSTANCE}
CEGA_ENDPOINT_PASSWORD=${CEGA_REST_PASSWORD}
CEGA_ENDPOINT_RESP_PASSWD=.password_hash
CEGA_ENDPOINT_RESP_PUBKEY=.pubkey
EOF

echomsg "\t* Elasticsearch configuration file"
cat > ${PRIVATE}/${INSTANCE}/logs/elasticsearch.yml <<EOF
cluster.name: local-ega
network.host: 0.0.0.0
http.port: 9200
EOF

echomsg "\t* Logstash configuration file"
cat > ${PRIVATE}/${INSTANCE}/logs/logstash.yml <<EOF
path.config: /usr/share/logstash/pipeline
http.host: "0.0.0.0"
http.port: 9600
EOF

cat > ${PRIVATE}/${INSTANCE}/logs/logstash.conf <<EOF
input {
	tcp {
		port => 5000
		codec => json {
            charset => "UTF-8"
        }
	}
}
output {
	elasticsearch {
		hosts => "ega-elasticsearch-${INSTANCE}:9200"
	}
}
EOF

echomsg "\t* Kibana configuration file"
cat > ${PRIVATE}/${INSTANCE}/logs/kibana.yml <<EOF
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.url: "http://ega-elasticsearch-${INSTANCE}:9200"
EOF

#########################################################################
# Keeping a trace of if
#########################################################################

cat >> ${PRIVATE}/${INSTANCE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/lib/instance.sh for INSTANCE ${INSTANCE}
#
#####################################################################
#
GPG_PASSPHRASE            = ${GPG_PASSPHRASE}
GPG_NAME                  = ${GPG_NAME}
GPG_COMMENT               = ${GPG_COMMENT}
GPG_EMAIL                 = ${GPG_EMAIL}
RSA_PASSPHRASE            = ${RSA_PASSPHRASE}
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
CEGA_PASSWORD             = ${CEGA_PASSWORD}
#
DOCKER_INBOX_PORT         = ${DOCKER_INBOX_PORT}
EOF
