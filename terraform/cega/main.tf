/* ====================================
   Main file for the Central EGA mockup
   ==================================== */

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
variable pubkey      {}
variable flavor      {}

terraform {
  backend "local" {
    path = ".terraform/cega.tfstate"
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

resource "openstack_compute_keypair_v2" "cega_key" {
  name       = "cega-key"
  public_key = "${var.pubkey}"
}

# ========= Network =========
resource "openstack_networking_network_v2" "cega_net" {
  name           = "cega-net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "cega_subnet" {
  network_id  = "${openstack_networking_network_v2.cega_net.id}"
  name        = "cega-subnet"
  cidr        = "192.168.100.0/24"
  enable_dhcp = true
  ip_version  = 4
  dns_nameservers = "${var.dns_servers}"
}

resource "openstack_networking_router_interface_v2" "cega_router_interface" {
  router_id = "${var.router_id}"
  subnet_id = "${openstack_networking_subnet_v2.cega_subnet.id}"
}

# ========= Security Groups =========

resource "openstack_compute_secgroup_v2" "cega" {
  name        = "cega"
  description = "Central EGA RabbitMQ and Users DB"

  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 5672
    to_port     = 5672
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

# ========= Machine =========

data "archive_file" "cega_users" {
  type        = "zip"
  output_path = "private/cega_users.zip"
  source_dir = "private/users"
}


data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    mq_conf     = "${base64encode("${file("${path.module}/rabbitmq.config")}")}"
    mq_defs     = "${base64encode("${file("private/defs.json")}")}"
    cega_env    = "${base64encode("${file("private/env")}")}"
    cega_server = "${base64encode("${file("${path.module}/server.py")}")}"
    cega_users  = "${base64encode("${file("${data.archive_file.cega_users.output_path}")}")}"
    cega_html   = "${base64encode("${file("${path.module}/users.html")}")}"
    ega_slice   = "${base64encode("${file("../systemd/ega.slice")}")}"
    ega_service = "${base64encode("${file("../systemd/cega-users.service")}")}"
  }
}

resource "openstack_compute_instance_v2" "cega" {
  name        = "cega"
  flavor_name = "${var.flavor}"
  image_name  = "EGA-cega"
  key_pair  = "${openstack_compute_keypair_v2.cega_key.name}"
  security_groups = ["default","${openstack_compute_secgroup_v2.cega.name}"]
  network {
    uuid = "${openstack_networking_network_v2.cega_net.id}"
    fixed_ip_v4 = "192.168.100.100"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "fip" {
  pool = "${var.pool}"
}
resource "openstack_compute_floatingip_associate_v2" "cega_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.fip.address}"
  instance_id = "${openstack_compute_instance_v2.cega.id}"
}

# output "cega" {
#   value = "${openstack_compute_instance_v2.cega.public_ip}"
# }
