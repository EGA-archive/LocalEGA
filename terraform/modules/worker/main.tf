variable count { default = 1 }
variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

resource "openstack_compute_instance_v2" "worker" {
  count     = "${var.count}"
  name      = "${format("worker-%02d", count.index+1)}"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  #user_data       = "${file("${path.module}/boot.sh")}"
  network { name = "${var.ega_net}" }
}

## Master GPG-agent

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
  #user_data       = "${file("${path.module}/keys.sh")}"
  network { name = "${var.ega_net}" }
}
