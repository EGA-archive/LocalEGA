#!/usr/bin/env bash

echomsg "Generating private data for ${INSTANCE} [Default in ${SETTINGS}/${INSTANCE}]"

########################################################
# Loading the instance's settings

if [[ -f ${SETTINGS}/${INSTANCE}.instance ]]; then
    source ${SETTINGS}/${INSTANCE}.instance
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

mkdir -p ${PRIVATE}/${INSTANCE}/{gpg,rsa,certs}
chmod 700 ${PRIVATE}/${INSTANCE}/{gpg,rsa,certs}

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

# Hack to avoid the "Socket name too long" error
GNUPGHOME=${PRIVATE}/${INSTANCE}/gpg
export GNUPGHOME
${GPG_AGENT} --daemon
${GPG} --batch --generate-key ${PRIVATE}/${INSTANCE}/gen_key
rm -f ${PRIVATE}/${INSTANCE}/gen_key
${GPG_CONF} --kill gpg-agent || :

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genrsa -out ${PRIVATE}/${INSTANCE}/rsa/ega.sec -passout pass:${RSA_PASSPHRASE} 2048
${OPENSSL} rsa -in ${PRIVATE}/${INSTANCE}/rsa/ega.sec -passin pass:${RSA_PASSPHRASE} -pubout -out ${PRIVATE}/${INSTANCE}/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/${INSTANCE}/certs/ssl.key -nodes -out ${PRIVATE}/${INSTANCE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* the EGA configuration files"
cat > ${PRIVATE}/${INSTANCE}/keys.conf <<EOF
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = ${RSA_PASSPHRASE}
EOF

cat > ${PRIVATE}/${INSTANCE}/ega.conf <<EOF
[DEFAULT]
log = debug

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

[outgestion]
# Keyserver communication
keyserver_host = ega_keys_${INSTANCE}
EOF


#########################################################################

echomsg "\t* Generating the configuration files"

cat >> ${PRIVATE}/cega/env <<EOF
CEGA_REST_${INSTANCE}_PASSWORD=${CEGA_REST_PASSWORD}
EOF

cat > ${PRIVATE}/${INSTANCE}/auth.conf <<EOF
debug = yes

##################
# Databases
##################
db_connection = host=ega_db_${INSTANCE} port=5432 dbname=lega user=${DB_USER} password=${DB_PASSWORD} connect_timeout=1 sslmode=disable

enable_rest = yes
rest_endpoint = http://cega/user/%s
rest_user = ${INSTANCE}
rest_password = ${CEGA_REST_PASSWORD}
rest_resp_passwd = .password_hash
rest_resp_pubkey = .pubkey

##################
# NSS Queries
##################
nss_get_user = SELECT elixir_id,'x',1000,1000,'EGA User','${INBOX_PATH}'|| elixir_id,'/sbin/nologin' FROM users WHERE elixir_id = \$1 LIMIT 1
nss_add_user = SELECT insert_user(\$1,\$2,\$3)

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = \$1 LIMIT 1
pam_acct = SELECT elixir_id FROM users WHERE elixir_id = \$1 and current_timestamp < last_accessed + expiration
EOF

function gather_worker_ips {
    for (( i=1; i<=${WORKERS}; i++)); do
	[[ ${i} > 1 ]] && echo -n ',' 
	echo -n "\"${PRIVATE_IPS[worker_${i}]}\""
    done
}

cat >> main.tf <<EOF

# ======== Definitions for ${INSTANCE} ===========

module "instance_${INSTANCE}" {
       source         = "./instances"
       instance_data  = "${PRIVATE}/${INSTANCE}"
       pubkey         = "${PUBKEY}"
       cidr           = "${CIDR}"
       dns_servers    = ${DNS_SERVERS}
       router_id      = "${ROUTER_ID}"

       db_user        = "${DB_USER}"
       db_password    = "${DB_PASSWORD}"
       db_name        = "lega"

       ip_db          = "${PRIVATE_IPS['db']}"
       ip_mq          = "${PRIVATE_IPS['mq']}"
       ip_inbox       = "${PRIVATE_IPS['inbox']}"
       ip_frontend    = "${PRIVATE_IPS['frontend']}"
       ip_monitors    = "${PRIVATE_IPS['monitors']}"
       ip_vault       = "${PRIVATE_IPS['vault']}"
       ip_keys        = "${PRIVATE_IPS['keys']}"
       ip_workers     = [$(gather_worker_ips)]

       greetings      = "${LEGA_GREETINGS}"

       inbox_size     = "${INBOX_SIZE}"
       inbox_path     = "${INBOX_PATH}"
       vault_size     = "${VAULT_SIZE}"

       gpg_passphrase = "${GPG_PASSPHRASE}"
}
EOF

# Recording private IPs
for k in ${!PRIVATE_IPS[@]}; do echo -e "${PRIVATE_IPS[${k}]}\tega_${k}_${INSTANCE}" >> ${PRIVATE}/hosts; done

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
CEGA_REST_PASSWORD        = ${CEGA_REST_PASSWORD}
CEGA_MQ_PASSWORD          = ${CEGA_MQ_PASSWORD}
EOF
