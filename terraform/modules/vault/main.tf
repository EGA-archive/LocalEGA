variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }
variable cloud_init { default = "${file("${path.module}/boot.sh")}" }

resource "openstack_compute_instance_v2" "vault" {
  name      = "vault"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network { name = "${var.ega_net}" }
  user_data       = "${var.cloud_init}"
}

resource "openstack_blockstorage_volume_v2" "vault" {
  name = "vault"
  description = "Da vault"
  size = 100
}

resource "openstack_compute_volume_attach_v2" "vault_attach" {
  instance_id = "${openstack_compute_instance_v2.vault.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.vault.id}"
}
