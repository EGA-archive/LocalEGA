/* ===================================
   Main file for the Local EGA project
   =================================== */

variable os_username {}
variable os_password {}
variable db_password {}
variable pubkey {}

variable rsa_home {}
variable gpg_home {}
variable gpg_certs {}
variable gpg_passphrase {}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "${var.os_username}"
  password    = "${var.os_password}"
  tenant_id   = "e62c28337a094ea99571adfb0b97939f"
  tenant_name = "SNIC 2017/13-34"
  auth_url    = "https://hpc2n.cloud.snic.se:5000/v3"
  region      = "HPC2N"
  domain_name = "snic"
}

# ========= Network =========
module "network" {
  source = "./network"
  cidr = "192.168.10.0/24"
}

# ========= Key Pair =========
resource "openstack_compute_keypair_v2" "ega_key" {
  name       = "ega_key"
  public_key = "${var.pubkey}"
}

# ========= Instances as Modules =========
module "db" {
  source = "./modules/db"
  db_password = "${var.db_password}"
  private_ip = "192.168.10.10"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "mq" {
  source = "./modules/mq"
  private_ip = "192.168.10.11"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "connectors" {
  source = "./modules/connectors"
  private_ip = "192.168.10.13"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "inbox" {
  source = "./modules/inbox"
  volume_size = 400
  private_ip = "192.168.10.14"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "frontend" {
  source = "./modules/frontend"
  private_ip = "192.168.10.15"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "monitors" {
  source = "./modules/monitors"
  private_ip = "192.168.10.16"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "vault" {
  source = "./modules/vault"
  volume_size = 400
  private_ip = "192.168.10.17"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "verify" {
  source = "./modules/verify"
  private_ip = "192.168.10.18"
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
}
module "workers" {
  source = "./modules/worker"
  count = 4
  private_ip_keys = "192.168.10.12"
  private_ips = ["192.168.10.100","192.168.10.101","192.168.10.102","192.168.10.103"]
  ega_key = "${openstack_compute_keypair_v2.ega_key.name}"
  rsa_home = "${var.rsa_home}"
  gpg_home = "${var.gpg_home}"
  gpg_passphrase = "${var.gpg_passphrase}"
  gpg_certs = "${var.gpg_certs}"
}
