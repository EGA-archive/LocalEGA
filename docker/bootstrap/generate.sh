#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

# Defaults:
VERBOSE=yes
FORCE=no
SSL_SUBJ="/C=SE/ST=Sweden/L=Uppsala/O=NBIS/OU=SysDevs/CN=LocalEGA/emailAddress=ega@nbis.se"
PRIVATE=private
DB_USER=postgres
DB_TRY=30
CEGA_MQ_USER=cega_sweden
CEGA_MQ_VHOST=se

GPG=gpg
GPG_NAME="EGA Sweden"
GPG_COMMENT="@NBIS"
GPG_EMAIL="ega@nbis.se"

OPENSSL=openssl

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <name>         \tName of the main folder for private data"
    echo -e "\t--force, -f                  \tForce the re-creation of the subfolders"
    echo ""
    echo -e "\t--gpg_exec <value>           \tgpg executable"
    echo -e "\t--openssl <value>            \topenssl executable"
    echo ""
    echo -e "\t--gpg_passphrase <value>     \tPassphrase at the GPG key creation"
    echo -e "\t--gpg_name <value>,"
    echo -e "\t--gpg_comment <value>,"
    echo -e "\t--gpg_email <value>          \tDetails for the GPG key"
    echo ""
    echo -e "\t--rsa_passphrase <value>     \tPassphrase at the RSA key creation"
    echo ""
    echo -e "\t--ssl_subj <value>           \tSubject for the SSL certificates"
    echo -e "\t                             \t[Default: ${SSL_SUBJ}]"
    echo ""
    echo -e "\t--db_user <value>,"
    echo -e "\t--db_password <value>        \tDatabase username and password"
    echo -e "\t--db_try <value>             \tDatabase connection attempts"
    echo -e "\t                             \t[User default: ${DB_USER} | Connection attempts default: ${DB_TRY}]"
    echo -e "\t--cega_mq_user <value>,"
    echo -e "\t--cega_mq_password <value>,"
    echo -e "\t--cega_mq_vhost <value>,     \tUsername, password, vhost for the Central EGA message broker"
    echo -e "\t                             \t[User default: ${CEGA_MQ_USER}, VHost default: ${CEGA_MQ_VHOST}]"
    echo ""
    echo -e "\t--quiet, -q                  \tRemoves the verbose output (and uses -f)"
    echo -e "\t--help, -h                   \tOutputs this message and exits"
    echo -e "\t-- ...                       \tAny other options appearing after the -- will be ignored"
    echo ""
}

# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --quiet|-q) VERBOSE=no;;
        --help|-h) usage; exit 0;;
        --force|-f) FORCE=yes;;
        --private_dir) PRIVATE=$2; shift;;
        --gpg_passphrase) GPG_PASSPHRASE=$2; shift;;
        --gpg_name) GPG_NAME=$2; shift;;
        --gpg_comment) GPG_COMMENT=$2; shift;;
        --gpg_email) GPG_EMAIL=$2; shift;;
        --gpg_exec) GPG=$2; shift;;
        --openssl) OPENSSL=$2; shift;;
        --rsa_passphrase) RSA_PASSPHRASE=$2; shift;;
        --ssl_subj) SSL_SUBJ=$2; shift;;
        --db_user) DB_USER=$2; shift;;
        --db_password) DB_PASSWORD=$2; shift;;
        --db_try) DB_TRY=$2; shift;;
	--cega_mq_user) CEGA_MQ_USER=$2; shift;;
	--cega_mq_password) CEGA_MQ_PASSWORD=$2; shift;;
	--cega_mq_vhost) CEGA_MQ_VHOST=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

exec 2>${HERE}/.err
[[ $VERBOSE == 'no' ]] && exec 1>${HERE}/.log && FORCE='yes'

[[ -x $(readlink ${GPG}) ]] && echo "${GPG} is not executable" && exit 2
[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable" && exit 3

#########################################################################
# Creating the necessary folders
# Ask recreate them if already existing
#########################################################################

case $PRIVATE in
    /*)  ABS_PRIVATE=$PRIVATE;;
    ./*|../*) ABS_PRIVATE=$PWD/$PRIVATE;;
    *) ABS_PRIVATE=$HERE/$PRIVATE;;
esac

if [[ -d $ABS_PRIVATE ]]; then
    if [[ $FORCE == 'yes' ]]; then
	rm -rf $ABS_PRIVATE
    else
	# Asking
	echo "[Warning] The folder \"$ABS_PRIVATE\" already exists. "
	while : ; do # while = In a subshell
	    echo -n "[Warning] "
	    echo -n -e "Proceed to re-create it? [y/N] "
	    read -t 10 yn
	    case $yn in
		y) rm -rf $ABS_PRIVATE; break;;
		N) echo "Ok. Choose another private directory. Exiting"; exit 1;;
		*) echo "Eh?";;
	    esac
	done
    fi
fi

mkdir -p $ABS_PRIVATE/{gpg,rsa,certs,cega/users,cega/mq,.env.d}

#########################################################################
# Generating the non-supplied values
#########################################################################

function generate_password {
    local size=${1:-16} # defaults to 16 characters
    p=$(python3.6 -c "import secrets,string;print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(${size})))")
    echo $p
}

[[ -z $GPG_PASSPHRASE ]] && GPG_PASSPHRASE=$(generate_password 16)
[[ -z $RSA_PASSPHRASE ]] && RSA_PASSPHRASE=$(generate_password 16)
[[ -z $DB_PASSWORD ]] && DB_PASSWORD=$(generate_password 16)
[[ -z $CEGA_MQ_PASSWORD ]] && CEGA_MQ_PASSWORD=$(generate_password 16)

EGA_USER_PASSWORD_JOHN=$(generate_password 16)
${OPENSSL} genrsa -out $ABS_PRIVATE/cega/users/john.sec -passout pass:${EGA_USER_PASSWORD_JOHN} 2048
${OPENSSL} rsa -in $ABS_PRIVATE/cega/users/john.sec -passin pass:${EGA_USER_PASSWORD_JOHN} -pubout -out $ABS_PRIVATE/cega/users/john.pub
chmod 400 $ABS_PRIVATE/cega/users/john.sec
EGA_USER_PUBKEY_JOHN=$(ssh-keygen -i -mPKCS8 -f $ABS_PRIVATE/cega/users/john.pub)

EGA_USER_PASSWORD_JANE=$(generate_password 16)
${OPENSSL} genrsa -out $ABS_PRIVATE/cega/users/jane.sec -passout pass:${EGA_USER_PASSWORD_JANE} 2048
${OPENSSL} rsa -in $ABS_PRIVATE/cega/users/jane.sec -passin pass:${EGA_USER_PASSWORD_JANE} -pubout -out $ABS_PRIVATE/cega/users/jane.pub
chmod 400 $ABS_PRIVATE/cega/users/jane.sec
EGA_USER_PUBKEY_JANE=$(ssh-keygen -i -mPKCS8 -f $ABS_PRIVATE/cega/users/jane.pub)

cat > $ABS_PRIVATE/.trace <<EOF
#
# Generated by bootstrap/generate.sh
#
PRIVATE                = ${PRIVATE}
GPG_PASSPHRASE         = ${GPG_PASSPHRASE}
GPG_NAME               = ${GPG_NAME}
GPG_COMMENT            = ${GPG_COMMENT}
GPG_EMAIL              = ${GPG_EMAIL}
GPG exec               = ${GPG}
RSA_PASSPHRASE         = ${RSA_PASSPHRASE}
SSL_SUBJ               = ${SSL_SUBJ}
OPENSSL exec           = ${OPENSSL}
DB_USER                = ${DB_USER}
DB_PASSWORD            = ${DB_PASSWORD}
DB_TRY                 = ${DB_TRY}
CEGA_MQ_USER           = ${CEGA_MQ_USER}
CEGA_MQ_PASSWORD       = ${CEGA_MQ_PASSWORD}
CEGA_MQ_VHOST          = ${CEGA_MQ_VHOST}
EGA_USER_PASSWORD_JOHN = ${EGA_USER_PASSWORD_JOHN}
EGA_USER_PUBKEY_JOHN   = ${EGA_USER_PUBKEY_JOHN}
EGA_USER_PASSWORD_JANE = ${EGA_USER_PASSWORD_JANE}
EGA_USER_PUBKEY_JANE   = ${EGA_USER_PUBKEY_JANE}
EOF
[[ $VERBOSE == 'yes' ]] && cat $ABS_PRIVATE/.trace

#########################################################################
# And....cue music
#########################################################################

echo -e "\nGenerating the GnuPG key"

cat > $ABS_PRIVATE/gen_key <<EOF
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

${GPG} --homedir $ABS_PRIVATE/gpg --batch --generate-key $ABS_PRIVATE/gen_key
chmod 700 $ABS_PRIVATE/gpg
rm -f $ABS_PRIVATE/gen_key

echo "Generating the RSA public and private key"
${OPENSSL} genrsa -out $ABS_PRIVATE/rsa/ega.sec -passout pass:${RSA_PASSPHRASE} 2048
${OPENSSL} rsa -in $ABS_PRIVATE/rsa/ega.sec -passin pass:${RSA_PASSPHRASE} -pubout -out $ABS_PRIVATE/rsa/ega.pub

echo "Generating the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout $ABS_PRIVATE/certs/ssl.key -nodes -out $ABS_PRIVATE/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

echo "Generating some fake EGA users"
cat > $ABS_PRIVATE/cega/users/john.yml <<EOF
---
password_hash: $(openssl passwd -1 $EGA_USER_PASSWORD_JOHN)
pubkey: ${EGA_USER_PUBKEY_JOHN}
EOF
cat > $ABS_PRIVATE/cega/users/jane.yml <<EOF
---
password_hash: $(openssl passwd -1 $EGA_USER_PASSWORD_JANE)
pubkey: ${EGA_USER_PUBKEY_JANE}
EOF

# Populate configs
echo "Creating the EGA configuration files"
cat > $ABS_PRIVATE/keys.conf <<EOF
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = ${RSA_PASSPHRASE}
EOF

cat > $ABS_PRIVATE/ega.conf <<EOF
[DEFAULT]
log = debug

[ingestion]
gpg_cmd = /usr/local/bin/gpg --homedir ~/.gnupg --decrypt %(file)s

## Connecting to Central EGA
[cega.broker]
host = cega_mq
username = ${CEGA_MQ_USER}
password = ${CEGA_MQ_PASSWORD}
vhost = ${CEGA_MQ_VHOST}
heartbeat = 0

[db]
host = ega_db
username = ${DB_USER}
password = ${DB_PASSWORD}
try = ${DB_TRY}
EOF

# Note: We could use a .env.d/cega_mq file with 
# RABBITMQ_DEFAULT_USER=...
# RABBITMQ_DEFAULT_PASSWORD=...
# RABBITMQ_DEFAULT_VHOST=...
# But then the queues and bindings are not properly set up
# Doing this instead:

echo "Hashing CEGA MQ passwords"
function rabbitmq_hash {
    # 1) Generate a random 32 bit salt
    # 2) Concatenate that with the UTF-8 representation of the password
    # 3) Take the SHA-256 hash
    # 4) Concatenate the salt again
    # 5) Convert to base64 encoding
    local SALT=${2:-$(${OPENSSL} rand -hex 4)}
    (
	printf $SALT | xxd -p -r
	( printf $SALT | xxd -p -r; printf $1 ) | ${OPENSSL} dgst -binary -sha256
    ) | base64
}

cat > $ABS_PRIVATE/cega/mq/defs.json <<EOF
{"rabbit_version":"3.6.11",
 "users":[{"name":"${CEGA_MQ_USER}", "password_hash":"$(rabbitmq_hash ${CEGA_MQ_PASSWORD} '908DC60A')", "hashing_algorithm":"rabbit_password_hashing_sha256", "tags":"administrator"}],
 "vhosts":[{"name":"${CEGA_MQ_VHOST}"}],
 "permissions":[{"user":"${CEGA_MQ_USER}" , "vhost":"${CEGA_MQ_VHOST}", "configure":".*", "write":".*", "read":".*"}],
 "parameters":[],
 "global_parameters":[{"name":"cluster_name", "value":"rabbit@localhost"}],
 "policies":[],
 "queues":[{"name":"sweden.v1.commands.file"     , "vhost":"${CEGA_MQ_VHOST}", "durable":true, "auto_delete":false, "arguments":{}},
	   {"name":"sweden.v1.commands.completed", "vhost":"${CEGA_MQ_VHOST}", "durable":true, "auto_delete":false, "arguments":{}}],
 "exchanges":[{"name":"localega.v1", "vhost":"${CEGA_MQ_VHOST}", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}],
 "bindings":[{"source":"localega.v1", "vhost":"${CEGA_MQ_VHOST}", "destination_type":"queue", "arguments":{},
	      "destination":"sweden.v1.commands.file", "routing_key":"sweden.file"},
	     {"source":"localega.v1", "vhost":"${CEGA_MQ_VHOST}", "destination_type":"queue", "arguments":{},
	      "destination":"sweden.v1.commands.completed", "routing_key":"sweden.file.completed"}]
}
EOF

# Populate env-settings for docker compose
echo "Creating the docker-compose configuration files"
cat > $ABS_PRIVATE/.env.d/db <<EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${DB_PASSWORD}
EOF
cat > $ABS_PRIVATE/.env.d/gpg <<EOF
GPG_PASSPHRASE=${GPG_PASSPHRASE}
EOF

echo -e "\nGeneration completed"
