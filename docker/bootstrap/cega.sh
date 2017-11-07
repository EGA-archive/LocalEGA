#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

source $HERE/lib.sh

# Defaults
VERBOSE=yes
FORCE=no
PRIVATE=private
DEFAULTS=$HERE/defaults/cega

function usage {
    echo "Usage: $0 [options] -- <instance>"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <name>         \tName of the main folder for private data"
    echo -e "\t--force, -f                  \tForce the re-creation of the subfolders"
    echo ""
    echo -e "\t--defaults <value>           \tDefaults data to be loaded [$DEFAULTS]"
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
        --defaults) DEFAULTS=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

if [[ -e $DEFAULTS ]];then
    source $DEFAULTS
else
    echo "Defaults not found"
    exit 1
fi

#[[ $VERBOSE == 'no' ]] && exec 1>${HERE}/.log && FORCE='yes'
exec 2>${HERE}/.err

case $PRIVATE in
    /*)  ABS_PRIVATE=$PRIVATE;;
    ./*|../*) ABS_PRIVATE=$PWD/$PRIVATE;;
    *) ABS_PRIVATE=$HERE/$PRIVATE;;
esac

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable" && exit 3

#########################################################################
# And....cue music
#########################################################################

rm_politely $ABS_PRIVATE/cega
mkdir -p $ABS_PRIVATE/cega/{users,mq}

echo -n "Generating data for a fake Central EGA"

echomsg "\t* fake EGA users"

EGA_USER_PASSWORD_JOHN=$(generate_password 16)
EGA_USER_PASSWORD_JANE=$(generate_password 16)
EGA_USER_PASSWORD_TAYLOR=$(generate_password 16)

EGA_USER_PUBKEY_JOHN=$ABS_PRIVATE/cega/users/john.pub
EGA_USER_SECKEY_JOHN=$ABS_PRIVATE/cega/users/john.sec

EGA_USER_PUBKEY_JANE=$ABS_PRIVATE/cega/users/jane.pub
EGA_USER_SECKEY_JANE=$ABS_PRIVATE/cega/users/jane.sec


${OPENSSL} genrsa -out ${EGA_USER_SECKEY_JOHN} -passout pass:${EGA_USER_PASSWORD_JOHN} 2048
${OPENSSL} rsa -in ${EGA_USER_SECKEY_JOHN} -passin pass:${EGA_USER_PASSWORD_JOHN} -pubout -out ${EGA_USER_PUBKEY_JOHN}
chmod 400 ${EGA_USER_SECKEY_JOHN}

${OPENSSL} genrsa -out ${EGA_USER_SECKEY_JANE} -passout pass:${EGA_USER_PASSWORD_JANE} 2048
${OPENSSL} rsa -in ${EGA_USER_SECKEY_JANE} -passin pass:${EGA_USER_PASSWORD_JANE} -pubout -out ${EGA_USER_PUBKEY_JANE}
chmod 400 ${EGA_USER_SECKEY_JANE}


cat > $ABS_PRIVATE/cega/users/john.yml <<EOF
---
password_hash: $(${OPENSSL} passwd -1 ${EGA_USER_PASSWORD_JOHN})
pubkey: $(ssh-keygen -i -mPKCS8 -f ${EGA_USER_PUBKEY_JOHN})
EOF

cat > $ABS_PRIVATE/cega/users/jane.yml <<EOF
---
pubkey: $(ssh-keygen -i -mPKCS8 -f ${EGA_USER_PUBKEY_JANE})
EOF

cat > $ABS_PRIVATE/cega/users/taylor.yml <<EOF
---
password_hash: $(${OPENSSL} passwd -1 ${EGA_USER_PASSWORD_TAYLOR})
EOF

mkdir -p $ABS_PRIVATE/cega/users/{swe1,fin1}
# They all have access to SWE1
pushd $ABS_PRIVATE/cega/users/swe1 > /dev/null
ln -s ../john.yml .
ln -s ../jane.yml .
ln -s ../taylor.yml .
popd > /dev/null
# John has also access to FIN1
pushd $ABS_PRIVATE/cega/users/fin1 > /dev/null
ln -s ../john.yml .
popd > /dev/null

#########################################################################

# Note: We could use a .env.d/cega_mq file with 
# RABBITMQ_DEFAULT_USER=...
# RABBITMQ_DEFAULT_PASSWORD=...
# RABBITMQ_DEFAULT_VHOST=...
# But then the queues and bindings are not properly set up
# Doing this instead:

echomsg "\t* a CEGA password for the MQ"

function output_password_hashes {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do 
	tmp+=("{\"name\":\"cega_$i\",\"password_hash\":\"$(rabbitmq_hash ${CEGA_MQ[$i]})\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":\"administrator\"}")
    done
    join_by ",\n" "${tmp[@]}"
}

function output_vhosts {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do 
	tmp+=("{\"name\":\"$i\"}")
    done
    join_by "," "${tmp[@]}"
}

function output_permissions {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do
	tmp+=("{\"user\":\"cega_$i\", \"vhost\":\"$i\", \"configure\":\".*\", \"write\":\".*\", \"read\":\".*\"}")
    done
    join_by $',\n' "${tmp[@]}"
}

function output_queues {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do
	tmp+=("{\"name\":\"$i.v1.commands.file\", \"vhost\":\"$i\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}}")
	tmp+=("{\"name\":\"$i.v1.commands.completed\", \"vhost\":\"$i\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}}")
    done
    join_by $',\n' "${tmp[@]}"
}

function output_exchanges {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do
	tmp+=("{\"name\":\"localega.v1\", \"vhost\":\"$i\", \"type\":\"topic\", \"durable\":true, \"auto_delete\":false, \"internal\":false, \"arguments\":{}}")
    done
    join_by $',\n' "${tmp[@]}"
}


function output_bindings {
    declare -a tmp
    for i in "${!CEGA_MQ[@]}"; do
	tmp+=("{\"source\":\"localega.v1\",\"vhost\":\"$i\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"$i.v1.commands.file\",\"routing_key\":\"$i.file\"}")
	tmp+=("{\"source\":\"localega.v1\",\"vhost\":\"$i\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"$i.v1.commands.completed\",\"routing_key\":\"$i.completed\"}")
    done
    join_by $',\n' "${tmp[@]}"
}

cat > $ABS_PRIVATE/cega/mq/defs.json <<EOF
{"rabbit_version":"3.6.11",
 "users":[$(output_password_hashes)],
 "vhosts":[$(output_vhosts)],
 "permissions":[$(output_permissions)],
 "parameters":[],
 "global_parameters":[{"name":"cluster_name", "value":"rabbit@localhost"}],
 "policies":[],
 "queues":[$(output_queues)],
 "exchanges":[$(output_exchanges)],
 "bindings":[$(output_bindings)]
}
EOF

#########################################################################
# Populate env-settings for docker compose
#########################################################################

rm_politely $ABS_PRIVATE/.env.d
mkdir -p $ABS_PRIVATE/.env.d

echomsg "Generating the docker-compose configuration files"

echo "LEGA_INSTANCES=${LEGA_INSTANCES}" > $ABS_PRIVATE/.env.d/cega_instances
for i in "${!CEGA_REST[@]}"; do
    tmp=CEGA_REST_${i}_PASSWORD
    echo "${tmp}=${CEGA_REST[$i]}" >> $ABS_PRIVATE/.env.d/cega_instances
done

for i in "${!CEGA_REST[@]}"; do
    mkdir $ABS_PRIVATE/.env.d/$i
    cat > $ABS_PRIVATE/.env.d/$i/cega <<EOF
LEGA_INSTANCE_GREETING=${LEGA_GREETINGS[$i]}
CEGA_ENDPOINT=http://cega_users/user/%s
CEGA_ENDPOINT_USER=${i}
CEGA_ENDPOINT_PASSWORD=${CEGA_REST[$i]}
CEGA_ENDPOINT_RESP_PASSWD=.password_hash
CEGA_ENDPOINT_RESP_PUBKEY=.pubkey
EOF
done

#########################################################################

task_complete "Generation completed for CentralEGA"

{
    cat <<EOF
#####################################################################
#
# Generated by bootstrap/cega.sh 
#
#####################################################################
#
PRIVATE                   = ${PRIVATE}
OPENSSL exec              = ${OPENSSL}
# =============================
EGA_USER_PASSWORD_JOHN    = ${EGA_USER_PASSWORD_JOHN}
EGA_USER_PUBKEY_JOHN      = <bootstrap>/$PRIVATE/cega/users/john.pub
EGA_USER_PUBKEY_JANE      = <bootstrap>/$PRIVATE/cega/users/jane.pub
EGA_USER_PASSWORD_TAYLOR  = ${EGA_USER_PASSWORD_TAYLOR}
# =============================
EOF

    for i in "${!CEGA_MQ[@]}"; do
	echo -e "CEGA_MQ_${i}_PASSWORD = ${CEGA_MQ[$i]}"
    done
    echo -e "# ============================="
    for i in "${!CEGA_REST[@]}"; do
	echo -e "CEGA_REST_${i}_PASSWORD = ${CEGA_REST[$i]}"
    done

    for i in "${!CEGA_REST[@]}"; do
	echo "# ============================="
	echo "CEGA_ENDPOINT for $i"
	echo "# ============================="
	cat $ABS_PRIVATE/.env.d/$i/cega
    done
} > $ABS_PRIVATE/.trace.cega
#[[ $VERBOSE == 'yes' ]] && cat $ABS_PRIVATE/.trace.cega
