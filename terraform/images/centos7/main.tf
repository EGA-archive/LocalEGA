/* ==================================
   Main file for the Local EGA images
   ================================== */

variable username    {}
variable password    {}
variable tenant_id   {}
variable tenant_name {}
variable auth_url    {}
variable region      {}
variable domain_name {}

variable boot_image  {}
variable router_id   {}
variable flavor      {}
variable key         {}

terraform {
  backend "local" {
    path = ".terraform/boot-ega.tfstate"
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

# ========= Network =========

resource "openstack_networking_network_v2" "boot_net" {
  name           = "boot-ega-net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "boot_subnet" {
  network_id  = "${openstack_networking_network_v2.boot_net.id}"
  name        = "boot-ega-subnet"
  cidr        = "192.168.1.0/24"
  enable_dhcp = true
  ip_version  = 4
  dns_nameservers = ["8.8.8.8"]
}

resource "openstack_networking_router_interface_v2" "boot_router_interface" {
  router_id = "${var.router_id}"
  subnet_id = "${openstack_networking_subnet_v2.boot_subnet.id}"
}


# ========= Instances =========

resource "openstack_compute_instance_v2" "common" {
  name            = "ega-common"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${var.key}"
  security_groups = ["default"]
  network {
    uuid          = "${openstack_networking_network_v2.boot_net.id}"
    fixed_ip_v4   = "192.168.1.200"
  }
  user_data       = "${file("${path.module}/common.sh")}"
}

resource "openstack_compute_instance_v2" "db" {
  name            = "ega-db"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${var.key}"
  security_groups = ["default"]
  network {
    uuid          = "${openstack_networking_network_v2.boot_net.id}"
    fixed_ip_v4   = "192.168.1.201"
  }
  user_data       = "${file("${path.module}/db.sh")}"
}

resource "openstack_compute_instance_v2" "mq" {
  name            = "ega-mq"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${var.key}"
  security_groups = ["default"]
  network {
    uuid          = "${openstack_networking_network_v2.boot_net.id}"
    fixed_ip_v4   = "192.168.1.202"
  }
  user_data       = "${file("${path.module}/mq.sh")}"
}

resource "openstack_compute_instance_v2" "cega" {
  name            = "cega"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${var.key}"
  security_groups = ["default"]
  network {
    uuid          = "${openstack_networking_network_v2.boot_net.id}"
    fixed_ip_v4   = "192.168.1.203"
  }
  user_data       = "${file("${path.module}/cega.sh")}"
}
