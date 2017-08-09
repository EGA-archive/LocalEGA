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
resource "openstack_compute_instance_v2" "test" {
  name      = "test"
  flavor_name = "ssc.small"
  image_name = "EGA-common"
  key_pair  = "ega_key"
  security_groups = ["default"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
}


module "inbox" {
  source = "./modules/inbox"
}
module "frontend" {
  source = "./modules/frontend"
}
module "connectors" {
  source = "./modules/connectors"
}
module "db" { 
  source = "./modules/db"
}
# module "monitors" {
#   source = "./modules/monitors"
# }
module "mq" {
  source = "./modules/mq"
}
module "vault" {
  source = "./modules/vault"
}
module "verify" {
  source = "./modules/verify"
}
module "workers" {
  source = "./modules/worker"
  count = 2
}

# # ========= /etc/hosts =========
# data "template_file" "hosts" {
#   template = "${file("${path.root}/hosts.tpl")}"

#   vars {
#     db     = "${module.db.openstack_compute_instance_v2.db.private_ip}"
#     mq     = "${module.mq.openstack_compute_instance_v2.mq.private_ip}"
#     keys   = "${module.workers.openstack_compute_instance_v2.keys.private_ip}"
#   }
# }

