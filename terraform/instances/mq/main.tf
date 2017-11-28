variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name {}
variable image_name { default = "EGA-mq" }

variable private_ip {}
variable cidr {}
variable instance_data {}

resource "openstack_compute_secgroup_v2" "ega_mq" {
  name        = "ega-mq"
  description = "RabbitMQ rules"

  rule {
    from_port   = 5672
    to_port     = 5672
    ip_protocol = "tcp"
    cidr        = "${var.cidr}"
  }
  rule {
    from_port   = 15672
    to_port     = 15672
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0" # Soon changed to "${var.cidr}"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    mq_defs     = "${base64encode("${file("${path.module}/defs.json")}")}"
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
  }
}

resource "openstack_compute_instance_v2" "mq" {
  name      = "mq"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_mq.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}
