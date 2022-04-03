#!/usr/bin/env bats
# -*- mode:shell-script -*-

load ../_common/helpers

# DB not reachable from ...
# -------------------------

@test "The database is not ping-able from inbox" {
    
    # Get the IP address of the database
    eval "DB_IP=$(docker inspect db | jq '.[0].NetworkSettings.Networks."lega_private-db".IPAddress')"
    # eval is there to remove the quotes around the value

    pushd ${DOCKER_PATH}
    run docker-compose exec inbox sh ping -c 4 ${DB_IP:-db}
    popd
    [ $status -ne 0 ]
}

@test "The database is not ping-able from the vault (if s3)" {

    if docker inspect archive &>/dev/null; then

	# Get the IP address of the database
	eval "DB_IP=$(docker inspect db | jq '.[0].NetworkSettings.Networks."lega_private-db".IPAddress')"
	# eval is there to remove the quotes around the value

	# Boot a container on the same network as the vault and ping the database by IP
	run docker run -it --rm --network=lega_private-vault alpine ping -c 4 ${DB_IP:-db}
	[ $status -ne 0 ]
    fi
}

# Vault not reachable from ...
# -------------------------

@test "The vault is not ping-able from the database (if s3)" {

    if docker inspect archive &>/dev/null; then

	# Get the IP address of the vault
	eval "VAULT_IP=$(docker inspect archive | jq '.[0].NetworkSettings.Networks."lega_private-vault".IPAddress')"
	pushd ${DOCKER_PATH}
	run docker-compose exec db sh ping -c 4 ${VAULT_IP:-archive}
	popd
	[ $status -ne 0 ]
    fi
}

@test "The vault is not ping-able from the inbox (if s3)" {

    if docker inspect archive &>/dev/null; then

	# Get the IP address of the vault
	eval "VAULT_IP=$(docker inspect archive | jq '.[0].NetworkSettings.Networks."lega_private-vault".IPAddress')"
	pushd ${DOCKER_PATH}
	run docker-compose exec inbox sh ping -c 4 ${VAULT_IP:-archive}
	popd
	[ $status -ne 0 ]
    fi
}
