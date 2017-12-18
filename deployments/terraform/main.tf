/* ===================================
   Main file for the Local EGA project
   =================================== */

variable username    {}
variable password    {}
variable tenant_id   {}
variable tenant_name {}
variable auth_url    {}
variable region      {}
variable domain_name {}
variable pool        {}
variable router_id   {}
variable dns_servers { type = "list" }
variable key         {}
variable flavor      {}
variable flavor_compute {}

terraform {
  backend "local" {
    path = ".terraform/ega.tfstate"
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "${var.username}"
  password    = "${var.password}"
  tenant_id   = "${var.tenant_id}"
  tenant_name = "${var.tenant_name}"
  auth_url    = "${var.auth_url}"
  region      = "${var.region}"
  domain_name = "${var.domain_name}"
}

# ========= Network LEGA =========

resource "openstack_networking_network_v2" "ega_net" {
  name           = "ega-net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "ega_subnet" {
  network_id  = "${openstack_networking_network_v2.ega_net.id}"
  name        = "ega-subnet"
  cidr        = "192.168.10.0/24"
  enable_dhcp = true
  ip_version  = 4
  dns_nameservers = "${var.dns_servers}"
}

resource "openstack_networking_router_interface_v2" "router_interface" {
  router_id = "${var.router_id}"
  subnet_id = "${openstack_networking_subnet_v2.ega_subnet.id}"
}

# ========= Instances =========

module "db" {
  source        = "./instances/db"
  private_ip    = "192.168.10.10"
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  cidr          = "192.168.10.0/24"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
}

module "mq" {
  source        = "./instances/mq"
  private_ip    = "192.168.10.11"
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  cidr          = "192.168.10.0/24"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
}

module "frontend" {
  source        = "./instances/frontend"
  private_ip    = "192.168.10.13"
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  pool          = "${var.pool}"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
}

module "inbox" {
  source        = "./instances/inbox"
  private_ip    = "192.168.10.12"
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  cidr          = "192.168.10.0/24"
  volume_size   = "300"
  pool          = "${var.pool}"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
}

module "vault" {
  source      = "./instances/vault"
  private_ip    = "192.168.10.14"
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  volume_size   = "150"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
}

module "workers" {
  source        = "./instances/workers"
  count         = 2
  private_ip_keys = "192.168.10.16"
  private_ips   = ["192.168.10.101","192.168.10.102"]
  ega_key       = "${var.key}"
  ega_net       = "${openstack_networking_network_v2.ega_net.id}"
  cidr          = "192.168.10.0/24"
  flavor_name   = "${var.flavor}"
  instance_data = "private"
  flavor_name_compute = "${var.flavor_compute}"
}
