#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

source $HERE/lib.sh

# Defaults
VERBOSE=no
FORCE=yes
PRIVATE=private

function usage {
    echo "Usage: $0 [options] -- <instance>"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <name>         \tName of the main folder for private data"
    echo ""
    echo -e "\t--verbose, -v                \tShow verbose output"
    echo -e "\t--polite, -p                 \tDo not force the re-creation of the subfolders. Ask instead"
    echo -e "\t--help, -h                   \tOutputs this message and exits"
    echo -e "\t-- ...                       \tAny other options appearing after the -- will be ignored"
    echo ""
}

# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage; exit 0;;
        --verbose|-v) VERBOSE=yes;;
        --polite|-p) FORCE=no;;
        --private_dir) PRIVATE=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

[[ $VERBOSE == 'yes' ]] && FORCE='no'

# Loading the instance's settings
INSTANCE=$1
[[ -z ${INSTANCE} ]] && usage && exit 1

if [[ -f $HERE/defaults/$INSTANCE ]]; then
    source $HERE/defaults/$INSTANCE
else
    echo "No settings found for $INSTANCE"
    exit 1
fi

#[[ $VERBOSE == 'no' ]] && exec 1>${HERE}/.log && FORCE='yes'
exec 2>${HERE}/.err

[[ -x $(readlink ${GPG}) ]] && echo "${GPG} is not executable" && exit 2
[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable" && exit 3

if [ -z "${DB_USER}" -o "${DB_USER}" == "postgres" ]; then
    echo "Choose a database user (but not 'postgres')"
    exit 4
fi

case $PRIVATE in
    /*)  ABS_PRIVATE=$PRIVATE;;
    ./*|../*) ABS_PRIVATE=$PWD/$PRIVATE;;
    *) ABS_PRIVATE=$HERE/$PRIVATE;;
esac

[[ ! -f $ABS_PRIVATE/.trace.cega ]] && echo "You must run $HERE/cega.sh first" && exit 1

#########################################################################
# And....cue music
#########################################################################

rm_politely $ABS_PRIVATE/$INSTANCE
mkdir -p $ABS_PRIVATE/$INSTANCE/{gpg,rsa,certs}

echo -n "Generating private data for ${INSTANCE^^}"

echomsg "\t* the GnuPG key"

cat > $ABS_PRIVATE/$INSTANCE/gen_key <<EOF
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

${GPG} --homedir $ABS_PRIVATE/$INSTANCE/gpg --batch --generate-key $ABS_PRIVATE/$INSTANCE/gen_key
chmod 700 $ABS_PRIVATE/$INSTANCE/gpg
rm -f $ABS_PRIVATE/$INSTANCE/gen_key

#########################################################################

echomsg "\t* the RSA public and private key"
${OPENSSL} genrsa -out $ABS_PRIVATE/$INSTANCE/rsa/ega.sec -passout pass:${RSA_PASSPHRASE} 2048
${OPENSSL} rsa -in $ABS_PRIVATE/$INSTANCE/rsa/ega.sec -passin pass:${RSA_PASSPHRASE} -pubout -out $ABS_PRIVATE/$INSTANCE/rsa/ega.pub

#########################################################################

echomsg "\t* the SSL certificates"
${OPENSSL} req -x509 -newkey rsa:2048 -keyout $ABS_PRIVATE/$INSTANCE/certs/ssl.key -nodes -out $ABS_PRIVATE/$INSTANCE/certs/ssl.cert -sha256 -days 1000 -subj ${SSL_SUBJ}

#########################################################################

echomsg "\t* the EGA configuration files"
cat > $ABS_PRIVATE/$INSTANCE/keys.conf <<EOF
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = ${RSA_PASSPHRASE}
EOF

CEGA_MQ_PASSWORD=$(awk "/CEGA_MQ_${INSTANCE}_PASSWORD/ { print \$3 }" $ABS_PRIVATE/.trace.cega)

cat > $ABS_PRIVATE/$INSTANCE/ega.conf <<EOF
[DEFAULT]
log = debug

[ingestion]
gpg_cmd = /usr/local/bin/gpg --homedir ~/.gnupg --decrypt %(file)s

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
# Populate env-settings for docker compose
#########################################################################

echomsg "Generating the docker-compose configuration files"

cat > $ABS_PRIVATE/.env.d/$INSTANCE/db <<EOF
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=lega
EOF

cat > $ABS_PRIVATE/.env.d/$INSTANCE/gpg <<EOF
GPG_PASSPHRASE=${GPG_PASSPHRASE}
EOF


#########################################################################

task_complete "Generation completed for ${INSTANCE^^}"


cat > $ABS_PRIVATE/.trace.$INSTANCE <<EOF
#####################################################################
#
# Generated by bootstrap/generate.sh -- $INSTANCE
#
#####################################################################
#
PRIVATE                   = ${PRIVATE}
GPG exec                  = ${GPG}
OPENSSL exec              = ${OPENSSL}
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
EOF
#[[ $VERBOSE == 'yes' ]] && cat $ABS_PRIVATE/.trace.$INSTANCE
