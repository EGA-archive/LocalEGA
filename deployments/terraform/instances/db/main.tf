variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name {}
variable image_name { default = "EGA-db" }

variable private_ip {}
variable cidr {}
variable instance_data {}

resource "openstack_compute_secgroup_v2" "ega_db" {
  name        = "ega-db"
  description = "Postgres DB"

  rule {
    from_port   = 5432
    to_port     = 5432
    ip_protocol = "tcp"
    cidr        = "${var.cidr}"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    db_sql      = "${base64encode("${file("${var.instance_data}/db.sql")}")}"
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    cidr        = "${var.cidr}"
  }
}

resource "openstack_compute_instance_v2" "db" {
  name            = "db"
  flavor_name     = "${var.flavor_name}"
  image_name      = "${var.image_name}"
  key_pair        = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_db.name}"]
  network {
    uuid          = "${var.ega_net}"
    fixed_ip_v4   = "${var.private_ip}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}
