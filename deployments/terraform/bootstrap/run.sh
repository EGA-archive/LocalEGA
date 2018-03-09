#!/usr/bin/env bash
set -e

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
SETTINGS=${HERE}/settings
PRIVATE=${HERE}/../private
EXTRAS=${HERE}/../../../extras

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value>   \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo ""
    echo -e "\t--settings <value>  \tPath to the settings the instances [Default: ${SETTINGS}]"
    echo ""
    echo -e "\t--verbose, -v       \tShow verbose output"
    echo -e "\t--polite, -p        \tDo not force the re-creation of the subfolders. Ask instead."
    echo -e "\t--help, -h          \tOutputs this message and exits"
    echo -e "\t-- ...              \tAny other options appearing after the -- will be ignored"
    echo ""
}

# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage; exit 0;;
        --verbose|-v) VERBOSE=yes;;
        --polite|-p) FORCE=no;;
        --openssl) OPENSSL=$2; shift;;
        --settings) SETTINGS=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source bootstrap/defs.sh

rm_politely ${PRIVATE} ${FORCE}
mkdir -p ${PRIVATE}

exec 2>${PRIVATE}/.err

########################################################
# Loading the settings
if [[ -f "${SETTINGS}" ]]; then
    source ${SETTINGS}
else
    error 1 "No settings found. Use settings.sample to create a settings file"
fi

[[ -x $(readlink ${OPENSSL}) ]] && error 3 "${OPENSSL} is not executable. Adjust the setting with --openssl"

[ -z "${DB_USER}" -o "${DB_USER}" == "postgres" ] && error 4 "Choose a database user (but not 'postgres')"

CEGA_PRIVATE=${HERE}/../cega/private
[[ ! -d "${CEGA_PRIVATE}" ]] && error 5 "You need to bootstrap Central EGA first"

if [ -z "${CEGA_CONNECTION}" ]; then
    error 6 "CEGA_CONNECTION should be set"
fi


#########################################################################
# And....cue music
#########################################################################

mkdir -p ${PRIVATE}/{pgp,rsa,certs}
chmod 700 ${PRIVATE}/{pgp,rsa,certs}

echomsg "\t* the PGP key"
# Python 3.6
python ${EXTRAS}/generate_pgp_key.py "${PGP_NAME}" "${PGP_EMAIL}" "${PGP_COMMENT}" --passphrase "${PGP_PASSPHRASE}" --pub ${PRIVATE}/pgp/ega.pub --priv ${PRIVATE}/pgp/ega.sec --armor
chmod 744 ${PRIVATE}/pgp/ega.pub

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genpkey -algorithm RSA -out ${PRIVATE}/rsa/ega.sec -pkeyopt rsa_keygen_bits:2048
${OPENSSL} rsa -pubout -in ${PRIVATE}/rsa/ega.sec -out ${PRIVATE}/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/certs/ssl.key -nodes -out ${PRIVATE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.conf"
cat > ${PRIVATE}/keys.conf <<EOF
[DEFAULT]
rsa : rsa.key.1
pgp : pgp.key.1

[rsa.key.1]
public : /etc/ega/rsa/ega.pub
private : /etc/ega/rsa/ega.sec

[pgp.key.1]
public : /etc/ega/pgp/ega.pub
private : /etc/ega/pgp/ega.sec
passphrase : ${PGP_PASSPHRASE}
expire: 30/MAR/19 08:00:00
EOF


CEGA_REST_PASSWORD=$(awk '/swe1_REST_PASSWORD/ {print $3}' ${CEGA_PRIVATE}/env)
[[ -z "${CEGA_REST_PASSWORD}" ]] && error 1 "Are you sure Central EGA is bootstrapped?"

echomsg "\t* ega.conf"
cat > ${PRIVATE}/ega.conf <<EOF
[DEFAULT]
log = debug

[ingestion]
inbox = /ega/inbox/%(user_id)s
# Keyserver communication
keyserver_endpoint_pgp = https://ega_keys/retrieve/pgp/%s
keyserver_endpoint_rsa = https://ega_keys/active/rsa
decrypt_cmd = python3.6 -u -m lega.openpgp %(file)s

## Connecting to Local EGA
[broker]
host = ega_mq
username = lega
password = ${MQ_PASSWORD}
vhost = /

[db]
host = ega_db
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}

[keyserver]
port = 8443
EOF


echomsg "\t* Generating auth.conf"
cat > ${PRIVATE}/auth.conf <<EOF
enable_cega = yes
cega_endpoint = http://cega/user/
cega_creds = swe1:${CEGA_REST_PASSWORD}
cega_json_passwd = .password_hash
cega_json_pubkey = .pubkey

##################
# NSS & PAM
##################
# prompt = Knock Knock:
ega_uid = ${EGA_UID}
ega_gid = ${EGA_GID}
# ega_gecos = EGA User
# ega_shell = /sbin/nologin

ega_dir = /ega/inbox
ega_dir_attrs = 2750 # rwxr-s---

##################
# FUSE mount
##################
ega_fuse_dir = /lega
ega_fuse_exec = /usr/bin/ega-fs
ega_fuse_flags = nodev,noexec,uid=${EGA_UID},gid=${EGA_GID},suid
EOF

echomsg "\t* Generating SSH banner"
cat > ${PRIVATE}/banner <<EOF
${LEGA_GREETINGS}
EOF


echomsg "\t* Generating db.sql"
cat > ${PRIVATE}/db.sql <<EOF
-- DROP USER IF EXISTS lega;
CREATE USER ${DB_USER} WITH password '${DB_PASSWORD}';

-- DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega WITH OWNER ${DB_USER};

EOF
cat ${EXTRAS}/db.sql >> ${PRIVATE}/db.sql
cat >> ${PRIVATE}/db.sql <<EOF

-- Changing the owner there too
ALTER TABLE files OWNER TO ${DB_USER};
ALTER TABLE users OWNER TO ${DB_USER};
ALTER TABLE errors OWNER TO ${DB_USER};
EOF

echomsg "\t* Generating ega_ssh_keys.sh"
cat > ${PRIVATE}/ega_ssh_keys.sh <<EOF
#!/bin/bash

eid=\${1%%@*} # strip what's after the @ symbol

query="SELECT pubkey from users where elixir_id = '\${eid}' LIMIT 1"

PGPASSWORD=${DB_PASSWORD} psql -tqA -U ${DB_USER} -h ega_db -d lega -c "\${query}"
EOF

echomsg "\t* MQ user"
cat > ${PRIVATE}/mq_users.sh <<EOF
#!/usr/bin/env bash
set -e

rabbitmqctl add_user lega ${MQ_PASSWORD}
rabbitmqctl set_user_tags lega administrator
rabbitmqctl set_permissions lega ".*" ".*" ".*" # -p /
EOF

cat > ${PRIVATE}/mq_lega.rc <<EOF
MQ_USER=lega
MQ_PASSWORD=${MQ_PASSWORD}
EOF

cat > ${PRIVATE}/mq_cega_defs.json <<EOF
{"parameters":[{"value": {"src-uri": "amqp://",
			  "src-exchange": "cega",
			  "src-exchange-key": "#",
			  "dest-uri": "${CEGA_CONNECTION}",
			  "dest-exchange": "localega.v1",
			  "add-forward-headers": false,
			  "ack-mode": "on-confirm",
			  "delete-after": "never"},
            	"vhost": "/",
		"component": "shovel",
		"name": "to-CEGA"},
	       {"value": {"src-uri": "amqp://",
			   "src-exchange": "lega",
			   "src-exchange-key": "completed",
			   "dest-uri": "amqp://",
			   "dest-exchange": "cega",
			   "dest-exchange-key": "files.completed",
			   "add-forward-headers": false,
			   "ack-mode": "on-confirm",
			   "delete-after": "never"},
		"vhost": "/",
		"component": "shovel",
		"name": "CEGA-completion"},
	       {"value":{"uri":"${CEGA_CONNECTION}",
			 "ack-mode":"on-confirm",
			 "trust-user-id":false,
			 "queue":"files"},
		"vhost":"/",
		"component":"federation-upstream",
		"name":"from-CEGA"}],
 "policies":[{"vhost":"/","name":"CEGA","pattern":"files","apply-to":"queues","definition":{"federation-upstream":"from-CEGA"},"priority":0}]
}
EOF

echomsg "\t* Kibana users credentials"
: > ${PRIVATE}/htpasswd
for u in ${!KIBANA_USERS[@]}; do echo "${u}:${KIBANA_USERS[$u]}" >> ${PRIVATE}/htpasswd; done

echomsg "\t* Logstash configuration"
cat > ${PRIVATE}/logstash.conf <<EOF
input {
	tcp {
		port => 5600
		codec => json { charset => "UTF-8" }
	}
	rabbitmq {
   		host => "ega_mq"
		port => 5672
		user => "lega"
		password => "${MQ_PASSWORD}"
		exchange => "amq.rabbitmq.trace"
		key => "#"
	}
}
output {
       if ("_jsonparsefailure" not in [tags]) {
	        elasticsearch {
			      hosts => ["localhost:9200"]
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

#########################################################################



#########################################################################

cat > ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/run.sh
#
#####################################################################
#
PGP_PASSPHRASE      = ${PGP_PASSPHRASE}
PGP_NAME            = ${PGP_NAME}
PGP_COMMENT         = ${PGP_COMMENT}
PGP_EMAIL           = ${PGP_EMAIL}
#
RSA_PASSPHRASE      = ${RSA_PASSPHRASE}
#
SSL_SUBJ            = ${SSL_SUBJ}
#
DB_USER             = ${DB_USER}
DB_PASSWORD         = ${DB_PASSWORD}
DB_TRY              = ${DB_TRY}
#
LEGA_GREETINGS      = ${LEGA_GREETINGS}
#
MQ_USER             = lega
MQ_PASSWORD         = ${MQ_PASSWORD}
MQ_VHOST            = /
#
CEGA_REST_PASSWORD  = ${CEGA_REST_PASSWORD}
CEGA_PASSWORD       = ${CEGA_PASSWORD}
#
KIBANA_USER         = lega
KIBANA_PASSWORD     = ${KIBANA_PASSWORD}
EOF

task_complete "Bootstrap complete"
