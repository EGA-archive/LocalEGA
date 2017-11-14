#!/usr/bin/env bash
set -e

HERE=$(dirname ${BASH_SOURCE[0]})
SETTINGS=${HERE}/settings
CREDS=${HERE}/../snic.rc
PRIVATE=private

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
    echo -e "\t--creds <value>     \tcredentials to load [Default: ${CREDS}]"
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
        --creds) CREDS=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source bootstrap/defs.sh

INSTANCES=$(cd ${SETTINGS}; ls *.instance | xargs) # make it one line. ls -lx didn't work
INSTANCES=(${INSTANCES//.instance/ })

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}/cega

exec 2>${PRIVATE}/.err

# Load the cega settings
if [[ -f ${CREDS} ]]; then
    source ${CREDS}
else
    echo "No credentials found"
    exit 1
fi
source ${SETTINGS}/cega

cat > main.tf <<EOF
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
  tenant_id   = "${TENANT_ID}"
  tenant_name = "${TENANT_NAME}"
  auth_url    = "${AUTH_URL}"
  region      = "${REGION}"
  domain_name = "${DOMAIN_NAME}"
}

module "cega" {
  source = "./instances/cega"
  private_ip  = "${CEGA_PRIVATE_IP}"
  cega_data = "${PRIVATE}/cega"
  pubkey = "${CEGA_PUBKEY}"
  cidr = "${CEGA_CIDR}"
  dns_servers = ${DNS_SERVERS}
  router_id = "${ROUTER_ID}"
}
EOF

# Recreating the hosts file
cat > ${PRIVATE}/hosts <<EOF
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

${CEGA_PRIVATE_IP}    cega central_ega
EOF

# And the CEGA files
{
    echo -n "LEGA_INSTANCES="
    join_by ',' ${INSTANCES[@]}
} > ${PRIVATE}/cega/env

# Central EGA Users
source bootstrap/cega_users.sh

# Generate the configuration for each instance
for INSTANCE in ${INSTANCES[@]}; do source bootstrap/instance.sh; done

# Central EGA Message Broker
source bootstrap/cega_mq.sh

task_complete "Bootstrap complete"
