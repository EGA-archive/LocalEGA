variable ega_key { default = "ega_key" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable count { default = 1 }

data "template_file" "cloud_init" {
  template = "${file("${path.root}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
  }
}

resource "openstack_compute_instance_v2" "worker" {
  count     = "${var.count}"
  name      = "${format("worker-%02d", count.index+1)}"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network { name = "ega_net" }
  user_data       = "${data.template_file.cloud_init.rendered}"
}

################################################################
##             Master GPG-agent
################################################################

data "template_file" "cloud_init_keys" {
  template = "${file("${path.root}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/keys.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
  }
}

resource "openstack_compute_secgroup_v2" "ega_gpg" {
  name        = "ega-gpg"
  description = "GPG socket forwarding"

  rule {
    from_port   = 9010
    to_port     = 9010
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "keys" {
  name      = "keys"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_gpg.name}"]
  network {
    name = "ega_net"
    fixed_ip_v4 = "192.168.10.12"
  }
  user_data       = "${data.template_file.cloud_init_keys.rendered}"
}
