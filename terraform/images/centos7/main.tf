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
variable boot_network{}
variable flavor      {}
variable pubkey      {}

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

resource "openstack_compute_keypair_v2" "boot_key" {
  name       = "boot-key"
  public_key = "${var.pubkey}"
}

# ========= Instances =========

resource "openstack_compute_instance_v2" "common" {
  name            = "ega-common"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${openstack_compute_keypair_v2.boot_key.name}"
  security_groups = ["default"]
  network { name  = "${var.boot_network}" }
  user_data       = "${file("${path.module}/common.sh")}"
}

resource "openstack_compute_instance_v2" "db" {
  name            = "ega-db"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${openstack_compute_keypair_v2.boot_key.name}"
  security_groups = ["default"]
  network { name  = "${var.boot_network}" }
  user_data       = "${file("${path.module}/db.sh")}"
}

resource "openstack_compute_instance_v2" "mq" {
  name            = "ega-mq"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${openstack_compute_keypair_v2.boot_key.name}"
  security_groups = ["default"]
  network { name  = "${var.boot_network}" }
  user_data       = "${file("${path.module}/mq.sh")}"
}

resource "openstack_compute_instance_v2" "cega" {
  name            = "cega"
  flavor_name     = "${var.flavor}"
  image_name      = "${var.boot_image}"
  key_pair        = "${openstack_compute_keypair_v2.boot_key.name}"
  security_groups = ["default"]
  network { name  = "${var.boot_network}" }
  user_data       = "${file("${path.module}/cega.sh")}"
}
