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

# ========= Network =========
resource "openstack_networking_network_v2" "ega_net" {
  name           = "ega_net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "ega_subnet" {
  network_id  = "${openstack_networking_network_v2.ega_net.id}"
  name        = "ega_subnet"
  cidr        = "192.168.10.0/24"
  enable_dhcp = false
  ip_version  = 4
  dns_nameservers = ["130.239.1.90","8.8.8.8"]
}

resource "openstack_networking_router_interface_v2" "ega_router_interface" {
  router_id = "1f852a3d-f7ea-45ae-9cba-3160c2029ba1"
  subnet_id = "${openstack_networking_subnet_v2.ega_subnet.id}"
}

# ========= Instances as Modules =========
module "db" {
  source = "./modules/db"
  db_password = "${var.db_password}"
  private_ip = "192.168.10.10"
}
module "mq" {
  source = "./modules/mq"
  private_ip = "192.168.10.11"
}
module "connectors" {
  source = "./modules/connectors"
  private_ip = "192.168.10.13"
}
module "inbox" {
  source = "./modules/inbox"
  volume_size = 400
  private_ip = "192.168.10.14"
}
module "frontend" {
  source = "./modules/frontend"
  private_ip = "192.168.10.15"
}
module "monitors" {
  source = "./modules/monitors"
  private_ip = "192.168.10.16"
}
module "vault" {
  source = "./modules/vault"
  volume_size = 400
  private_ip = "192.168.10.17"
}
module "verify" {
  source = "./modules/verify"
  private_ip = "192.168.10.18"
}
module "workers" {
  source = "./modules/worker"
  count = 2
  private_ip_keys = "192.168.10.12"
  private_ips = ["192.168.10.100","192.168.10.101"]
}
