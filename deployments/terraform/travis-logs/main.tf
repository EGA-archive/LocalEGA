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
variable key         {}
variable flavor      {}
variable kibana_passwd {}

terraform {
  backend "local" {
    path = ".terraform/travis_logs.tfstate"
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
resource "openstack_networking_network_v2" "travis_logs_net" {
  name           = "travis-logs-net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "travis_logs_subnet" {
  network_id  = "${openstack_networking_network_v2.travis_logs_net.id}"
  name        = "travis-logs-subnet"
  cidr        = "192.168.101.0/24"
  enable_dhcp = true
  ip_version  = 4
  dns_nameservers = "${var.dns_servers}"
}

resource "openstack_networking_router_interface_v2" "travis_logs_router_interface" {
  router_id = "${var.router_id}"
  subnet_id = "${openstack_networking_subnet_v2.travis_logs_subnet.id}"
}

# ========= Security Groups =========

resource "openstack_compute_secgroup_v2" "travis_logs" {
  name        = "travis_logs"
  description = "Travis Logs"

  rule {
    from_port   = 5600
    to_port     = 5600
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}


# ========= Machine =========
data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot = "${base64encode("${file("${path.module}/boot.sh")}")}"
    kibana_passwd = "${var.kibana_passwd}"
  }
}

resource "openstack_compute_instance_v2" "travis_logs" {
  name        = "travis_logs"
  flavor_name = "${var.flavor}"
  image_name  = "CentOS 7 - latest"
  key_pair  = "${var.key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.travis_logs.name}"]
  network {
    uuid = "${openstack_networking_network_v2.travis_logs_net.id}"
    fixed_ip_v4 = "192.168.101.100"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "fip" {
  pool = "${var.pool}"
}
resource "openstack_compute_floatingip_associate_v2" "travis_logs_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.fip.address}"
  instance_id = "${openstack_compute_instance_v2.travis_logs.id}"
}

output "address" {
  value = "${openstack_networking_floatingip_v2.fip.address}"
}
