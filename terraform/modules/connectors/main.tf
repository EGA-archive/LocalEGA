variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable hosts {}

data "template_file" "cloud_init" {
  template = "${file("${path.root}/cloud_init.tpl")}"

  vars {
    boot_script = "${file("${path.module}/boot.sh")}"
    host_file   = "${var.hosts}"
  }
}

resource "openstack_compute_instance_v2" "connectors" {
  name      = "connectors"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network {
    name = "ega_net"
    fixed_ip_v4 = "192.169.10.10"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}
