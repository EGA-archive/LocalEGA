#!/usr/bin/env bash
set -e

HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../private
MAIN_TF=${HERE}/../main.tf
LIB=${HERE}/lib
SETTINGS=${HERE}/settings

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
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${LIB}/defs.sh

INSTANCES=$(ls ${SETTINGS}/instances | xargs) # make it one line. ls -lx didn't work

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}/cega

exec 2>${PRIVATE}/.err

# Load the cega settings
source ${SETTINGS}/cega

cat > ${MAIN_TF} <<EOF
/* ===================================
   Main file for the Local EGA project
   =================================== */

variable os_username {}
variable os_password {}
variable tenant_id {}
variable tenant_name {}
variable auth_url {}
variable region {}
variable domain_name {}
variable router_id {}
variable dns_servers { type = list }

terraform {
  backend "local" {
    path = ".terraform/ega.tfstate"
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "\${var.os_username}"
  password    = "\${var.os_password}"
  tenant_id   = "\${var.tenant_id}"
  tenant_name = "\${var.tenant_name}"
  auth_url    = "\${var.auth_url}"
  region      = "\${var.region}"
  domain_name = "\${var.domain_name}"
}

module "cega" {
  source = "./cega"
  private_ip  = "${CEGA_PRIVATE_IP}"
  cega_data = "${PRIVATE}/cega"
  pubkey = "${CEGA_PUBKEY}"
  cidr = "${CEGA_CIDR}"
  dns_servers = \${var.dns_servers}
  router_id = "\${var.router_id}"
}

EOF

# Recreating the hosts file
echo -e "${CEGA_PRIVATE_IP}\tcega" > ${PRIVATE}/hosts

# And the CEGA files
echo "LEGA_INSTANCES=${INSTANCES// /,}" > ${PRIVATE}/cega/env

# Central EGA Users
source ${LIB}/cega_users.sh

# Generate the configuration for each instance
for INSTANCE in ${INSTANCES}; do source ${LIB}/instance.sh; done

# Central EGA Message Broker
source ${LIB}/cega_mq.sh

task_complete "Bootstrap complete"
