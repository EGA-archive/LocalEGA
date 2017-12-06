variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name {}
variable image_name { default = "EGA-common" }

variable private_ip {}
variable instance_data {}
variable pool {}

resource "openstack_compute_secgroup_v2" "ega_web" {
  name        = "ega-web"
  description = "Web rules"

  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 443
    to_port     = 443
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    lega_conf   = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    ega_options = "${base64encode("${file("${path.root}/systemd/options")}")}"
    ega_slice   = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
    ega_service = "${base64encode("${file("${path.root}/systemd/ega-frontend.service")}")}"
  }
}

resource "openstack_compute_instance_v2" "frontend" {
  name      = "frontend"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_web.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "fip" {
  pool = "${var.pool}"
}
resource "openstack_compute_floatingip_associate_v2" "frontend_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.fip.address}"
  instance_id = "${openstack_compute_instance_v2.frontend.id}"
}
