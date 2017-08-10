variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }
variable cloud_init { default = "${file("${path.module}/boot.sh")}" }

resource "openstack_compute_secgroup_v2" "ega_sftp" {
  name        = "ega-sftp"
  description = "SFTP access"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "inbox" {
  name      = "inbox"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_sftp.name}"]
  network { name = "${var.ega_net}" }
  user_data       = "${var.cloud_init}"
}

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "inbox_ip" {
  pool = "Public External IPv4 Network"
}
resource "openstack_compute_floatingip_associate_v2" "inbox_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.inbox_ip.address}"
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
}

# ===== Staging area / Inbox volume =====
resource "openstack_blockstorage_volume_v2" "staging" {
  name = "staging"
  description = "Inbox and Staging area"
  size = 100
}
resource "openstack_compute_volume_attach_v2" "inbox_attach" {
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.staging.id}"
}
