/* ===================================
   Main file for the Local EGA project
   =================================== */


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

# ========= Key Pair =========
resource "openstack_compute_keypair_v2" "ega_key" {
  name       = "ega_key"
  public_key = "${var.pubkey}"
}

# ========= Instances as Modules =========
# module "ega_network" {
#   source = "./network"
# }

# ========= Instances as Modules =========
module "connectors" {
  source = "./modules/test"
}
# module "connectors" {
#   source = "./modules/connectors"
# }
# module "db" {
#   source = "./modules/db"
# }
# module "mq" {
#   source = "./modules/mq"
# }
# module "inbox" {
#   source = "./modules/inbox"
# }
# module "frontend" {
#   source = "./modules/frontend"
# }
# # module "monitors" {
# #   source = "./modules/monitors"
# # }
# module "vault" {
#   source = "./modules/vault"
# }
# module "verify" {
#   source = "./modules/verify"
# }
# module "workers" {
#   source = "./modules/worker"
#   count = 2
# }
