variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name {}
variable image_name { default = "EGA-monitor" }

variable private_ip {}
variable instance_data {}
variable pool {}

resource "openstack_compute_secgroup_v2" "ega_monitor" {
  name        = "ega-monitor"
  description = "EGA Monitoring and Logging"

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

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    users       = "${base64encode("${file("${var.instance_data}/htpasswd")}")}"
    logstash    = "${base64encode("${file("${var.instance_data}/logstash.conf")}")}"
    es          = "${base64encode("${file("${path.module}/elasticsearch.yml")}")}"
    kibana      = "${base64encode("${file("${path.module}/kibana.yml")}")}"
  }
}

resource "openstack_compute_instance_v2" "ega_monitor" {
  name      = "monitor"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_monitor.name}"]
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
resource "openstack_compute_floatingip_associate_v2" "monitor_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.fip.address}"
  instance_id = "${openstack_compute_instance_v2.ega_monitor.id}"
}

output "address" {
  value = "${openstack_networking_floatingip_v2.fip.address}"
}
