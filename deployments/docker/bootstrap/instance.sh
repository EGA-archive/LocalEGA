#!/usr/bin/env bash

[[ -z "${INSTANCE}" ]] && echo 'The variable INSTANCE must be defined' 1>&2 && exit 1

########################################################
# Loading the instance's settings

if [[ -f ${SETTINGS}/${INSTANCE} ]]; then
    source ${SETTINGS}/${INSTANCE}
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

python3.6 ${HERE}/generate_pgp_key.py "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --prefix ${PRIVATE}/${INSTANCE}/pgp/ega --armor

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genpkey -algorithm RSA -out ${PRIVATE}/${INSTANCE}/rsa/ega.sec -pkeyopt rsa_keygen_bits:2048
${OPENSSL} rsa -pubout -in ${PRIVATE}/${INSTANCE}/rsa/ega.sec -out ${PRIVATE}/${INSTANCE}/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/${INSTANCE}/certs/ssl.key -nodes -out ${PRIVATE}/${INSTANCE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.conf"
cat > ${PRIVATE}/${INSTANCE}/keys.conf <<EOF
[REENCRYPTION_KEYS]
active = rsa.key.1

[PGP]
active = pgp.key.1
EXPIRE = 31/DEC/18 23:59:59

[rsa.key.1]
PATH = /etc/ega/rsa/sec.pem

[rsa.key.2]
PATH = /etc/ega/rsa/sec2.pem

[pgp.key.1]
public = /etc/ega/pgp/pub.pem
private = /etc/ega/pgp/sec.pem
passphrase = ${PGP_PASSPHRASE}
EOF

echomsg "\t* ega.conf"
cat > ${PRIVATE}/${INSTANCE}/ega.conf <<EOF
[DEFAULT]
log = /etc/ega/logger.yml

[ingestion]
# Keyserver communication
keyserver_host = ega-keys-${INSTANCE}

## Connecting to Local EGA
[broker]
host = ega-mq-${INSTANCE}

[db]
host = ega-db-${INSTANCE}
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}
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

cat >> ${PRIVATE}/cega/env <<EOF
CEGA_REST_${INSTANCE}_PASSWORD=${CEGA_REST_PASSWORD}
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

echomsg "\t* Elasticsearch configuration file"
cat > ${PRIVATE}/${INSTANCE}/logs/elasticsearch.yml <<EOF
cluster.name: local-ega
network.host: 0.0.0.0
http.port: 9200
EOF

echomsg "\t* Logstash configuration files"
cat > ${PRIVATE}/${INSTANCE}/logs/logstash.yml <<EOF
path.config: /usr/share/logstash/pipeline
http.host: "0.0.0.0"
http.port: 9600
EOF

cat > ${PRIVATE}/${INSTANCE}/logs/logstash.conf <<EOF
input {
	tcp {
		port => 5600
		codec => json { charset => "UTF-8" }
	}
	rabbitmq {
   		host => "mq-${INSTANCE}"
		port => 5672
		user => "guest"
		password => "guest"
		exchange => "amq.rabbitmq.trace"
		key => "#"
	}
}
output {
       if ("_jsonparsefailure" not in [tags]) {
	        elasticsearch {
			      hosts => ["ega-elasticsearch-${INSTANCE}:9200"]
		}

	} else {
		file {
			path => ["logs/error-%{+YYYY-MM-dd}.log"]
		}
		# output to console for debugging purposes
		stdout {
			codec => rubydebug
		}
	}
}
EOF

echomsg "\t* Kibana configuration file"
cat > ${PRIVATE}/${INSTANCE}/logs/kibana.yml <<EOF
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.url: "http://ega-elasticsearch-${INSTANCE}:9200"
EOF


# For the moment, still using guest:guest
echomsg "\t* Local broker to Central EGA broker credentials"
cat > ${PRIVATE}/${INSTANCE}/mq.env <<EOF
CEGA_CONNECTION=amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega-mq:5672/${INSTANCE}
EOF

#########################################################################
# Creating the docker-compose file
#########################################################################
cat >> ${PRIVATE}/ega_${INSTANCE}.yml <<EOF
version: '3.2'

networks:
  lega_${INSTANCE}:
    # user overlay in swarm mode
    # default is bridge
    driver: bridge
  cega:
    external: true

services:

  ############################################
  # Local EGA instance ${INSTANCE}
  ############################################

  # Local Message broker
  mq-${INSTANCE}:
    env_file: ${INSTANCE}/mq.env
    hostname: ega-mq-${INSTANCE}
    ports:
      - "${DOCKER_PORT_mq}:15672"
    image: nbisweden/ega-mq
    container_name: ega-mq-${INSTANCE}
    restart: on-failure:3
    # Required external link
    external_links:
      - cega-mq:cega-mq
    networks:
      - lega_${INSTANCE}
      - cega

  # Postgres Database
  db-${INSTANCE}:
    env_file: ${INSTANCE}/db.env
    hostname: ega-db-${INSTANCE}
    container_name: ega-db-${INSTANCE}
    image: postgres:latest
    volumes:
      - ./${INSTANCE}/db.sql:/docker-entrypoint-initdb.d/ega.sql:ro
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}

  # SFTP inbox
  inbox-${INSTANCE}:
    hostname: ega-inbox
    depends_on:
      - mq-${INSTANCE}
    # Required external link
    external_links:
      - cega-users:cega-users
    env_file:
      - ${INSTANCE}/db.env
      - ${INSTANCE}/cega.env
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    container_name: ega-inbox-${INSTANCE}
    image: nbisweden/ega-inbox
    # privileged, cap_add and devices cannot be used by docker Swarm
    privileged: true
    cap_add:
      - ALL
    devices:
      - /dev/fuse
    volumes:
      - ./${INSTANCE}/ega.conf:/etc/ega/conf.ini:ro
      - ./${INSTANCE}/logger.yml:/etc/ega/logger.yml:ro
      - inbox_${INSTANCE}:/ega/inbox
      # - ../..:/root/.local/lib/python3.6/site-packages:ro
      # - ~/_auth_ega:/root/auth
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}
      - cega

  # Vault
  vault-${INSTANCE}:
    depends_on:
      - db-${INSTANCE}
      - mq-${INSTANCE}
      - inbox-${INSTANCE}
    hostname: ega-vault
    container_name: ega-vault-${INSTANCE}
    image: nbisweden/ega-vault
    # Required external link
    external_links:
      - cega-mq:cega-mq
    environment:
      - MQ_INSTANCE=ega-mq-${INSTANCE}
      - CEGA_INSTANCE=cega-mq
    volumes:
       - staging_${INSTANCE}:/ega/staging
       - vault_${INSTANCE}:/ega/vault
       - ./${INSTANCE}/ega.conf:/etc/ega/conf.ini:ro
       - ./${INSTANCE}/logger.yml:/etc/ega/logger.yml:ro
       # - ../..:/root/.local/lib/python3.6/site-packages:ro
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}
      - cega

  # Ingestion Workers
  ingest-${INSTANCE}:
    depends_on:
      - db-${INSTANCE}
      - mq-${INSTANCE}
      - keys-${INSTANCE}
    image: nbisweden/ega-worker
    # Required external link
    external_links:
      - cega-mq:cega-mq
    environment:
      - MQ_INSTANCE=ega-mq-${INSTANCE}
      - CEGA_INSTANCE=cega-mq
      - KEYSERVER_HOST=ega-keys-${INSTANCE}
      - KEYSERVER_PORT=9010
    volumes:
       - inbox_${INSTANCE}:/ega/inbox
       - staging_${INSTANCE}:/ega/staging
       - ./${INSTANCE}/ega.conf:/etc/ega/conf.ini:ro
       - ./${INSTANCE}/logger.yml:/etc/ega/logger.yml:ro
       - ./${INSTANCE}/certs/ssl.cert:/etc/ega/ssl.cert:ro
       # - ../..:/root/.local/lib/python3.6/site-packages:ro
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}
      - cega

  # Key server
  keys-${INSTANCE}:
    env_file: ${INSTANCE}/pgp.env
    environment:
      - KEYSERVER_PORT=9010
    hostname: ega-keys-${INSTANCE}
    container_name: ega-keys-${INSTANCE}
    image: nbisweden/ega-keys
    tty: true
    expose:
      - "9010"
      - "9011"
    volumes:
       - ./${INSTANCE}/ega.conf:/etc/ega/conf.ini:ro
       - ./${INSTANCE}/logger.yml:/etc/ega/logger.yml:ro
       - ./${INSTANCE}/keys.conf:/etc/ega/keys.ini:ro
       - ./${INSTANCE}/certs/ssl.cert:/etc/ega/ssl.cert:ro
       - ./${INSTANCE}/certs/ssl.key:/etc/ega/ssl.key:ro
       - ./${INSTANCE}/pgp/ega.pub:/etc/ega/pgp/pub.pem:ro
       - ./${INSTANCE}/pgp/ega.sec:/etc/ega/pgp/sec.pem:ro
       - ./${INSTANCE}/rsa/ega.pub:/etc/ega/rsa/pub.pem:ro
       - ./${INSTANCE}/rsa/ega.sec:/etc/ega/rsa/sec.pem:ro
       - ../../../lega:/root/.local/lib/python3.6/site-packages/lega
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}

  # Logging & Monitoring (ELK: Elasticsearch, Logstash, Kibana).
  elasticsearch-${INSTANCE}:
    image: docker.elastic.co/elasticsearch/elasticsearch-oss:6.0.0
    container_name: ega-elasticsearch-${INSTANCE}
    volumes:
      - ./${INSTANCE}/logs/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
      - elasticsearch_${INSTANCE}:/usr/share/elasticsearch/data
    environment:
      ES_JAVA_OPTS: "-Xmx256m -Xms256m"
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}

  logstash-${INSTANCE}:
    image: docker.elastic.co/logstash/logstash-oss:6.0.0
    container_name: ega-logstash-${INSTANCE}
    volumes:
      - ./${INSTANCE}/logs/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./${INSTANCE}/logs/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
    environment:
      LS_JAVA_OPTS: "-Xmx256m -Xms256m"
    depends_on:
      - elasticsearch-${INSTANCE}
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}

  kibana-${INSTANCE}:
    image: docker.elastic.co/kibana/kibana-oss:6.0.0
    container_name: ega-kibana-${INSTANCE}
    volumes:
      - ./${INSTANCE}/logs/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
    ports:
      - "${DOCKER_PORT_kibana}:5601"
    depends_on:
      - elasticsearch-${INSTANCE}
      - logstash-${INSTANCE}
    restart: on-failure:3
    networks:
      - lega_${INSTANCE}

# Use the default driver for volume creation
volumes:
  inbox_${INSTANCE}:
  staging_${INSTANCE}:
  vault_${INSTANCE}:
  elasticsearch_${INSTANCE}:
EOF

echo -n ":private/ega_${INSTANCE}.yml" >> ${DOT_ENV} # no newline

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
DOCKER_PORT_inbox         = ${DOCKER_PORT_inbox}
DOCKER_PORT_mq            = ${DOCKER_PORT_mq}
DOCKER_PORT_kibana        = ${DOCKER_PORT_kibana}
EOF
