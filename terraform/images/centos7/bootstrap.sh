#!/usr/bin/env bash
set -e

HERE=$(dirname ${BASH_SOURCE[0]})
CREDS=${HERE}/../../snic.rc

# Defaults
VERBOSE=no
FORCE=yes

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo ""
    echo -e "\t--creds <value>     \tPath to the credentials to the cloud [Default: ${CREDS}]"
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
        --creds) CREDS=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${HERE}/../../bootstrap/defs.sh

# Loading the credentials
if [[ -f "${CREDS}" ]]; then
    source ${CREDS}
else
    echo "No credentials found"
    exit 1
fi

SETTINGS=$(basename ${CREDS})
if [[ -f "${SETTINGS}" ]]; then
    source ${SETTINGS}
else
    echo "No settings found [in ${SETTINGS}]"
    exit 1
fi

echomsg "\t* Create Terraform configuration"
cat > ${HERE}/main.tf <<EOF
/* ==================================
   Main file for the Local EGA images
   ================================== */

terraform {
  backend "local" {
    path = ".terraform/ega-images.tfstate"
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

# ========= Instances =========

resource "openstack_compute_instance_v2" "common" {
  name            = "ega-common"
  flavor_name     = "${FLAVOR}"
  image_name      = "${IMAGE}"
  key_pair        = "\${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "${NETWORK}" }
  user_data       = "\${file("\${path.module}/common.sh")}"
}

resource "openstack_compute_instance_v2" "db" {
  name            = "ega-db"
  flavor_name     = "${FLAVOR}"
  image_name      = "${IMAGE}"
  key_pair        = "\${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "${NETWORK}" }
  user_data       = "\${file("\${path.module}/db.sh")}"
}

resource "openstack_compute_instance_v2" "mq" {
  name            = "ega-mq"
  flavor_name     = "${FLAVOR}"
  image_name      = "${IMAGE}"
  key_pair        = "\${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "${NETWORK}" }
  user_data       = "\${file("\${path.module}/mq.sh")}"
}

resource "openstack_compute_instance_v2" "cega" {
  name            = "cega"
  flavor_name     = "${FLAVOR}"
  image_name      = "${IMAGE}"
  key_pair        = "\${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "${NETWORK}" }
  user_data       = "\${file("\${path.module}/cega.sh")}"
}
EOF

task_complete "Bootstrap images complete"
