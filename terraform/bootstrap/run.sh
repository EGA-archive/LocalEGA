#!/usr/bin/env bash
set -e

HERE=$(dirname ${BASH_SOURCE[0]})
CREDS=${HERE}/../snic.rc
SETTINGS=${HERE}/settings.rc
PRIVATE=${HERE}/../private

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl
GPG=gpg
GPG_CONF=gpgconf
GPG_AGENT=gpg-agent

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value>   \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--gpg <value>       \tPath to the GnuPG executable [Default: ${GPG}]"
    echo -e "\t--gpgconf <value>   \tPath to the GnuPG conf executable [Default: ${GPG_CONF}]"
    echo -e "\t--gpg-agent <value> \tPath to the GnuPG agent executable [Default: ${GPG_AGENT}]"
    echo ""
    echo -e "\t--creds <value>     \tPath to the credentials to the cloud [Default: ${CREDS}]"
    echo -e "\t--settings <value>  \tPath to the settings the instances [Default: ${SETTINGS}]"
    echo ""
    echo -e "\t--verbose, -v       \tShow verbose output"
    echo -e "\t--polite, -p        \tDo not force the re-creation of the subfolders. Ask instead"
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
	--gpg) GPG=$2; shift;;
	--gpgconf) GPG_CONF=$2; shift;;
        --openssl) OPENSSL=$2; shift;;
        --settings) SETTINGS=$2; shift;;
        --creds) CREDS=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source bootstrap/defs.sh

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}

exec 2>${PRIVATE}/.err

# Loading the credentials
if [[ -f "${CREDS}" ]]; then
    source ${CREDS}
else
    echo "No credentials found"
    exit 1
fi

########################################################
# Loading the settings
if [[ -f "${SETTINGS}" ]]; then
    source ${SETTINGS}
else
    echo "No settings found"
    exit 1
fi

[[ -x $(readlink ${GPG}) ]] && echo "${GPG} is not executable. Adjust the setting with --gpg" && exit 2
[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

if [ -z "${DB_USER}" -o "${DB_USER}" == "postgres" ]; then
    echo "Choose a database user (but not 'postgres')"
    exit 4
fi

CEGA_PRIVATE=${HERE}/../cega/private
[[ ! -d "${CEGA_PRIVATE}" ]] && echo "You need to bootstrap Central EGA first" && exit 5

#########################################################################
# And....cue music
#########################################################################

mkdir -p ${PRIVATE}/{gpg,rsa,certs}
chmod 700 ${PRIVATE}/{gpg,rsa,certs}

echomsg "\t* the GnuPG key"

cat > ${PRIVATE}/gen_key <<EOF
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
GNUPGHOME=${PRIVATE}/gpg
export GNUPGHOME
${GPG_AGENT} --daemon
${GPG} --batch --generate-key ${PRIVATE}/gen_key
rm -f ${PRIVATE}/gen_key
${GPG_CONF} --kill gpg-agent || :

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genrsa -out ${PRIVATE}/rsa/ega.sec -passout pass:${RSA_PASSPHRASE} 2048
${OPENSSL} rsa -in ${PRIVATE}/rsa/ega.sec -passin pass:${RSA_PASSPHRASE} -pubout -out ${PRIVATE}/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout ${PRIVATE}/certs/ssl.key -nodes -out ${PRIVATE}/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* keys.conf"
cat > ${PRIVATE}/keys.conf <<EOF
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = ${RSA_PASSPHRASE}
EOF


CEGA_REST_PASSWORD=$(awk '/swe1_REST_PASSWORD/ {print $3}' ${CEGA_PRIVATE}/env)
CEGA_MQ_PASSWORD=$(awk '/swe1_MQ_PASSWORD/ {print $3}' ${CEGA_PRIVATE}/.trace)
CEGA_PRIVATE_IP=$(awk '/PRIVATE_IP/ {print $3}' ${CEGA_PRIVATE}/.trace)
[[ -z "${CEGA_REST_PASSWORD}" ]] && echo "Are you sure Central EGA is bootstrapped?" && exit 1
[[ -z "${CEGA_MQ_PASSWORD}" ]] && echo "Are you sure Central EGA is bootstrapped?" && exit 1

echomsg "\t* ega.conf"
cat > ${PRIVATE}/ega.conf <<EOF
[DEFAULT]
log = debug

[ingestion]
gpg_cmd = gpg2 --decrypt %(file)s

# Keyserver communication
keyserver_host = ega_keys

## Connecting to Local EGA
[local.broker]
host = ega_mq

## Connecting to Central EGA
[cega.broker]
host = cega_mq
username = cega_swe1
password = ${CEGA_MQ_PASSWORD}
vhost = swe1
heartbeat = 0

file_queue = swe1.v1.commands.file
file_routing = swe1.completed

[db]
host = ega_db
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}

[frontend]
host = ega_frontend

[outgestion]
# Keyserver communication
keyserver_host = ega_keys
EOF

EGA_USER=1001
EGA_GROUP=1001 # I don't like that solution

echomsg "\t* Generating auth.conf"
cat > ${PRIVATE}/auth.conf <<EOF
debug = yes

##################
# Databases
##################
db_connection = host=ega_db port=5432 dbname=lega user=${DB_USER} password=${DB_PASSWORD} connect_timeout=1 sslmode=disable

enable_rest = yes
rest_endpoint = http://cega/user/%s
rest_user = swe1
rest_password = ${CEGA_REST_PASSWORD}
rest_resp_passwd = .password_hash
rest_resp_pubkey = .pubkey

##################
# NSS Queries
##################
nss_get_user = SELECT elixir_id,'x',${EGA_USER},${EGA_GROUP},'EGA User','${INBOX_PATH}'|| elixir_id,'/sbin/nologin' FROM users WHERE elixir_id = \$1 LIMIT 1
nss_add_user = SELECT insert_user(\$1,\$2,\$3)

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = \$1 LIMIT 1
pam_acct = SELECT elixir_id FROM users WHERE elixir_id = \$1 and current_timestamp < last_accessed + expiration
EOF

echomsg "\t* Generating SSH banner"
cat > ${PRIVATE}/banner <<EOF
${LEGA_GREETINGS}
EOF

echomsg "\t* Generating hosts"
cat > ${PRIVATE}/hosts <<EOF
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

${CEGA_PRIVATE_IP}    cega central_ega
EOF
for k in ${!PRIVATE_IPS[@]}; do echo -e "${PRIVATE_IPS[${k}]}\tega_${k}" >> ${PRIVATE}/hosts; done

echomsg "\t* Generating hosts.allow"
cat > ${PRIVATE}/hosts.allow <<EOF
sshd: ${CIDR}       : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed local)")&  : ALLOW
sshd: .es           : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .es)")&    : ALLOW
sshd: .cat          : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .cat)")&   : ALLOW
sshd: .se           : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .se)")&    : ALLOW
ALL : ALL           : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (denied)")&         : DENY
EOF

echomsg "\t* Generating db.sql"
cat > ${PRIVATE}/db.sql <<EOF
CREATE USER ${DB_USER} WITH password '${DB_PASSWORD}';
DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;
EOF
cat ${HERE}/../../docker/images/db/db.sql >> ${PRIVATE}/db.sql

echomsg "\t* GnuPG preset script"
cat > ${PRIVATE}/preset.sh <<EOF
#!/bin/bash
set -e
KEYGRIP=\$(gpg -k --with-keygrip ${GPG_EMAIL} | awk '/Keygrip/{print \$3;exit;}')
if [ ! -z "\$KEYGRIP" ]; then 
    echo 'Unlocking the GPG key'
    # This will use the standard socket. The proxy forwards to the extra socket.
    /usr/local/libexec/gpg-preset-passphrase --preset -P "${GPG_PASSPHRASE}" \$KEYGRIP
else
    echo 'Skipping the GPG key preseting'
fi
EOF

#########################################################################

function gather_worker_ips {
    for (( i=1; i<=${WORKERS}; i++)); do
	[[ ${i} > 1 ]] && echo -n ',' 
	echo -n "\"${PRIVATE_IPS[worker_${i}]}\""
    done
}

echomsg "\t* Create Terraform configuration"
cat > ${HERE}/main.tf <<EOF
/* ===================================
   Main file for the Local EGA project
   =================================== */

terraform {
  backend "local" {
    path = ".terraform/ega.tfstate"
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "${OS_USERNAME}"
  password    = "${OS_PASSWORD}"
  tenant_id   = "${OS_PROJECT_ID}"
  tenant_name = "${OS_PROJECT_NAME}"
  auth_url    = "${OS_AUTH_URL}"
  region      = "${OS_REGION_NAME}"
  domain_name = "${OS_USER_DOMAIN_NAME}"
}

resource "openstack_compute_keypair_v2" "ega_key" {
  name       = "ega-key"
  public_key = "${PUBKEY}"
}

module "network" {
  source        = "./network"
  cidr          = "${CIDR}"
  router_id     = "${ROUTER_ID}"
  dns_servers   = ${DNS_SERVERS}
}

module "db" {
  source        = "./instances/db"
  private_ip    = "${PRIVATE_IPS['db']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  cidr          = "${CIDR}"
  instance_data = "${PRIVATE}"
}

module "mq" {
  source        = "./instances/mq"
  private_ip    = "${PRIVATE_IPS['mq']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  cidr          = "${CIDR}"
  instance_data = "${PRIVATE}"
}

module "frontend" {
  source        = "./instances/frontend"
  private_ip    = "${PRIVATE_IPS['frontend']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  pool          = "${POOL}"
  instance_data = "${PRIVATE}"
}

module "inbox" {
  source        = "./instances/inbox"
  private_ip    = "${PRIVATE_IPS['inbox']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  cidr          = "${CIDR}"
  volume_size   = "${INBOX_SIZE}"
  pool          = "${POOL}"
  instance_data = "${PRIVATE}"
}

module "vault" {
  source      = "./instances/vault"
  private_ip    = "${PRIVATE_IPS['vault']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  volume_size   = "${VAULT_SIZE}"
  instance_data = "${PRIVATE}"
}

module "workers" {
  source        = "./instances/workers"
  count         = ${WORKERS}
  private_ip_keys = "${PRIVATE_IPS['keys']}"
  private_ips   = [$(gather_worker_ips)]
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  cidr          = "${CIDR}"
  instance_data = "${PRIVATE}"
}

module "monitors" {
  source        = "./instances/monitors"
  private_ip    = "${PRIVATE_IPS['monitors']}"
  ega_key       = "\${openstack_compute_keypair_v2.ega_key.name}"
  ega_net       = "\${module.network.ega_net_id}"
  cidr          = "${CIDR}"
  instance_data = "${PRIVATE}"
}
EOF


cat > ${PRIVATE}/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/run.sh
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

task_complete "Bootstrap complete"
