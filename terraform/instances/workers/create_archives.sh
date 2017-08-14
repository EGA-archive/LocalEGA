#!/bin/bash

gpg_home=$2
rsa_home=$3
certs_home=$4

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

if [ $1 == 'keys' ]; then

    pushd ${gpg_home}
    _GPG=$(zip - pubring.kbx trustdb.gpg openpgp-revocs.d/*.rev private-keys-v1.d/*.key | base64)
    popd
    pushd ${rsa_home}
    _RSA=$(zip - ega-public.pem ega.pem | base64)
    popd
    pushd ${certs_home}
    _CERTS=$(zip - *.cert *.key | base64)
    popd

    jq -n --arg gpg "$_GPG" --arg rsa "$_RSA" --arg certs "$_CERTS" '{ "gpg": $gpg, "rsa": $rsa, "certs": $certs}'

fi

if [ $1 == 'worker' ]; then

    pushd ${gpg_home}
    _GPG=$(zip - pubring.kbx trustdb.gpg | base64)
    popd
    pushd ${rsa_home}
    _RSA=$(zip - ega-public.pem ega.pem | base64) # ega.pem will be removed
    popd
    pushd ${certs_home}
    _CERTS=$(zip - *.cert | base64)
    popd

    jq -n --arg gpg "$_GPG" --arg rsa "$_RSA" --arg certs "$_CERTS" '{ "gpg": $gpg, "rsa": $rsa, "certs": $certs}'

fi

