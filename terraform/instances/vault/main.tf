variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }
variable volume_size { default = 100 }

variable private_ip {}
variable instance_data {}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    hosts       = "${base64encode("${file("${var.instance_data}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${var.instance_data}/hosts.allow")}")}"
    conf        = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    ega_options = "${base64encode("${file("${path.root}/systemd/options")}")}"
    ega_slice   = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
    ega_verify  = "${base64encode("${file("${path.root}/systemd/ega-verify.service")}")}"
    ega_vault   = "${base64encode("${file("${path.root}/systemd/ega-vault.service")}")}"
  }

}

resource "openstack_compute_instance_v2" "vault" {
  name      = "vault"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}

resource "openstack_blockstorage_volume_v2" "vault" {
  name = "vault"
  description = "Da vault"
  size = "${var.volume_size}"
}

resource "openstack_compute_volume_attach_v2" "vault_attach" {
  instance_id = "${openstack_compute_instance_v2.vault.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.vault.id}"
}
