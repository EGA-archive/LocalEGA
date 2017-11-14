#!/usr/bin/env bash
set -e

echomsg "Generating passwords for the Message Broker"

function rabbitmq_hash {
    # 1) Generate a random 32 bit salt
    # 2) Concatenate that with the UTF-8 representation of the password
    # 3) Take the SHA-256 hash
    # 4) Concatenate the salt again
    # 5) Convert to base64 encoding
    local SALT=${2:-$(${OPENSSL:-openssl} rand -hex 4)}
    {
	printf ${SALT} | xxd -p -r
	( printf ${SALT} | xxd -p -r; printf $1 ) | ${OPENSSL:-openssl} dgst -binary -sha256
    } | base64
}

function output_password_hashes {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do 
	CEGA_MQ_PASSWORD=$(awk -F= '/CEGA_MQ_PASSWORD/{print $2}' ${PRIVATE}/${INSTANCE}/.trace)
	CEGA_MQ_HASH=$(rabbitmq_hash $CEGA_MQ_PASSWORD)
	tmp+=("{\"name\":\"cega_${INSTANCE}\",\"password_hash\":\"${CEGA_MQ_HASH}\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":\"administrator\"}")
    done
    join_by ",\n" "${tmp[@]}"
}

function output_vhosts {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do 
	tmp+=("{\"name\":\"${INSTANCE}\"}")
    done
    join_by "," "${tmp[@]}"
}

function output_permissions {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do 
	tmp+=("{\"user\":\"cega_${INSTANCE}\", \"vhost\":\"${INSTANCE}\", \"configure\":\".*\", \"write\":\".*\", \"read\":\".*\"}")
    done
    join_by $',\n' "${tmp[@]}"
}

function output_queues {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do
	tmp+=("{\"name\":\"${INSTANCE}.v1.commands.file\",      \"vhost\":\"${INSTANCE}\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}}")
	tmp+=("{\"name\":\"${INSTANCE}.v1.commands.completed\", \"vhost\":\"${INSTANCE}\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}}")
    done
    join_by $',\n' "${tmp[@]}"
}

function output_exchanges {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do
	tmp+=("{\"name\":\"localega.v1\", \"vhost\":\"${INSTANCE}\", \"type\":\"topic\", \"durable\":true, \"auto_delete\":false, \"internal\":false, \"arguments\":{}}")
    done
    join_by $',\n' "${tmp[@]}"
}


function output_bindings {
    declare -a tmp=()
    for INSTANCE in ${INSTANCES}
    do
	tmp+=("{\"source\":\"localega.v1\",\"vhost\":\"${INSTANCE}\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"${INSTANCE}.v1.commands.file\",\"routing_key\":\"${INSTANCE}.file\"}")
	tmp+=("{\"source\":\"localega.v1\",\"vhost\":\"${INSTANCE}\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"${INSTANCE}.v1.commands.completed\",\"routing_key\":\"${INSTANCE}.completed\"}")
    done
    join_by $',\n' "${tmp[@]}"
}

mkdir -p ${PRIVATE}/cega
{
    echo    '{"rabbit_version":"3.6.11",'
    echo -n ' "users":['; output_password_hashes; echo '],'
    echo -n ' "vhosts":['; output_vhosts; echo '],'
    echo -n ' "permissions":['; output_permissions; echo '],'
    echo    ' "parameters":[],'
    echo -n ' "global_parameters":[{"name":"cluster_name", "value":"rabbit@localhost"}],'
    echo    ' "policies":[],'
    echo -n ' "queues":['; output_queues; echo '],'
    echo -n ' "exchanges":['; output_exchanges; echo '],'
    echo -n ' "bindings":['; output_bindings; echo ']'
    echo    '}'
} > ${PRIVATE}/cega/defs.json

