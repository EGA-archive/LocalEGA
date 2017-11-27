variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable private_ip {}
variable lega_conf {}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${var.lega_conf}"
  }
}

resource "openstack_compute_instance_v2" "connectors" {
  name      = "connectors"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}
