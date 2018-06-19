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
cat > ${PRIVATE}/lega/keys.ini <<EOF
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
log = console

[keyserver]
port = 8443

[quality_control]
keyserver_endpoint = https://keys:8443/retrieve/%s/private

[inbox]
location = /ega/inbox/%s
mode = 2750

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

# echomsg "\t* SFTP Inbox port"

echomsg "\t* db.sql"
# Running in container
cat /tmp/db.sql >> ${PRIVATE}/lega/db.sql


#########################################################################
# Populate env-settings for docker compose
#########################################################################

echomsg "\t* Elasticsearch configuration file"
cat > ${PRIVATE}/lega/logs/elasticsearch.yml <<EOF
cluster.name: local-ega
network.host: 0.0.0.0
http.port: 9200
EOF

echomsg "\t* Logstash configuration files"
cat > ${PRIVATE}/lega/logs/logstash.yml <<EOF
path.config: /usr/share/logstash/pipeline
http.host: "0.0.0.0"
http.port: 9600
EOF

cat > ${PRIVATE}/lega/logs/logstash.conf <<EOF
input {
	tcp {
		port => 5600
		codec => json { charset => "UTF-8" }
	}
	rabbitmq {
   		host => "mq"
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
			      hosts => ["elasticsearch:9200"]
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
cat > ${PRIVATE}/lega/logs/kibana.yml <<EOF
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.url: "http://elasticsearch:9200"
EOF


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
    hostname: db
    container_name: db
    image: postgres:latest
    volumes:
      - ./lega/db.sql:/docker-entrypoint-initdb.d/ega.sql:ro
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
    environment:
      - DB_INSTANCE=db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=lega
      - CEGA_ENDPOINT=http://cega-users/user/
      - CEGA_ENDPOINT_CREDS=lega:${CEGA_REST_PASSWORD}
      - CEGA_ENDPOINT_JSON_PASSWD=.password_hash
      - CEGA_ENDPOINT_JSON_PUBKEY=.pubkey
    ports:
      - "${DOCKER_PORT_inbox}:9000"
    container_name: inbox
    image: nbisweden/ega-inbox
    # privileged, cap_add and devices cannot be used by docker Swarm
    privileged: true
    cap_add:
      - ALL
    devices:
      - /dev/fuse
    volumes:
      - ./lega/conf.ini:/etc/ega/conf.ini:ro
      - inbox:/ega/inbox
      - ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
      - ../images/inbox/entrypoint.sh:/usr/bin/ega-entrypoint.sh
      #- ~/_auth_ega:/root/_auth_ega
    restart: on-failure:3
    networks:
      - lega
      - cega
    entrypoint: ["/bin/bash", "/usr/bin/ega-entrypoint.sh"]

  # Ingestion Workers
  ingest:
    depends_on:
      - db
      - mq
    image: nbisweden/ega-base
    container_name: ingest
    environment:
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}
    volumes:
       - inbox:/ega/inbox
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
       - ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
       #- ~/_cryptor/legacryptor:/root/.local/lib/python3.6/site-packages/legacryptor
    restart: on-failure:3
    networks:
      - lega
    entrypoint: ["gosu", "lega", "ega-ingest"]

  # Key server
  keys:
    hostname: keys
    container_name: keys
    image: nbisweden/ega-base
    expose:
      - "8443"
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
    volumes:
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
       - ./lega/keys.ini:/etc/ega/keys.ini:ro
       - ./lega/certs/ssl.cert:/etc/ega/ssl.cert:ro
       - ./lega/certs/ssl.key:/etc/ega/ssl.key:ro
       - ./lega/pgp/ega.sec:/etc/ega/pgp/ega.sec:ro
       - ./lega/pgp/ega2.sec:/etc/ega/pgp/ega2.sec:ro
       - ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega
    restart: on-failure:3
    external_links:
      - cega-eureka:cega-eureka
    networks:
      - lega
      - cega
    entrypoint: ["gosu","lega","ega-keyserver","--keys","/etc/ega/keys.ini"]

  # Quality Control
  qc:
    depends_on:
      - db
      - mq
      - inbox
      - keys
    hostname: qc
    container_name: qc
    image: nbisweden/ega-qc
    environment:
      - LEGA_PASSWORD=${LEGA_PASSWORD}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - DB_INSTANCE=db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=lega
    volumes:
       - ./lega/conf.ini:/etc/ega/conf.ini:ro
    restart: on-failure:3
    networks:
      - lega

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
    ports:
      - "${DOCKER_PORT_s3}:9000"
    command: server /data

# Use the default driver for volume creation
volumes:
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
EOF
